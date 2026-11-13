<#
.SYNOPSIS
  Bump the version, then check, build and test both implementations.

.DESCRIPTION
  Every run is a build and gets a new version (docs/versioning.md): VERSION at the repo root is read,
  bumped with Get-NextVersion, written back, and stamped into the Python package. The .NET build
  reads VERSION itself. Then runs, stopping at the first failure:
    Python: ruff check, ruff format --check, mypy, pytest, conformance (report in reports/python.json)
            and every vector generator's --check
    .NET:   build, test, format --verify-no-changes, conformance (report in reports/dotnet.json)
    Both:   the two reports diffed, each config in vectors/links run in both languages and compared,
            and signal files written by each language read by both and compared
  CI does not run this script and never bumps; it builds the committed version. The bump happens
  before the checks, so a failed build still uses up its number (numbers are never reused).

.PARAMETER Jobs
  Limit .NET build and test parallelism (passes -m:N and MaxCpuCount=N). Default: no limit.

.PARAMETER NoBump
  Check and test without making a new version (for a quick re-run; not for a build you keep).
#>
param(
    [int]$Jobs = 0,
    [switch]$NoBump
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot

function Get-NextVersion([string]$current) {
    $today = Get-Date
    $todayKey = [int]$today.ToString('yyyyMMdd')
    $y, $m, $d, $n = $current.Split('.') | ForEach-Object { [int]$_ }
    if ($y * 10000 + $m * 100 + $d -ge $todayKey) {      # same day (or a later date): bump N
        return "$y.$m.$d.$($n + 1)"
    }
    return "$($today.Year).$($today.Month).$($today.Day).0"   # first build today
}

function Invoke-Step([string]$name, [scriptblock]$command) {
    Write-Host "== $name" -ForegroundColor Cyan
    & $command
    if ($LASTEXITCODE -ne 0) { throw "$name failed (exit $LASTEXITCODE)" }
}

# Version: VERSION is the source of truth; the Python package gets a stamped copy.
$versionFile = Join-Path $root 'VERSION'
if (-not (Test-Path $versionFile)) { throw "VERSION not found at $versionFile" }
$current = [IO.File]::ReadAllText($versionFile).Trim()
if ($current -notmatch '^[1-9]\d{3}\.[1-9]\d?\.[1-9]\d?\.(0|[1-9]\d*)$') {
    throw "VERSION '$current' is not YYYY.M.D.N (docs/versioning.md)"
}
$version = if ($NoBump) { $current } else { Get-NextVersion $current }
if (-not $NoBump) { [IO.File]::WriteAllText($versionFile, "$version`n") }
$init = Join-Path $root 'python/src/signalforge/__init__.py'
$text = [IO.File]::ReadAllText($init)
$stamped = [regex]::Replace($text, '(?m)^__version__ = "[^"]*"', "__version__ = `"$version`"")
if ($stamped -ne $text) { [IO.File]::WriteAllText($init, $stamped) }
Write-Host "SignalForge $version" -ForegroundColor Green

$bin = if ($IsWindows -or $env:OS -eq 'Windows_NT') { 'Scripts' } else { 'bin' }
$venv = Join-Path $root ".venv/$bin"

Push-Location (Join-Path $root 'python')
try {
    Invoke-Step 'ruff check' { & "$venv/ruff" check . }
    Invoke-Step 'ruff format' { & "$venv/ruff" format --check . }
    Invoke-Step 'mypy' { & "$venv/mypy" }
    Invoke-Step 'pytest' { & "$venv/python" -m pytest -q }
    Invoke-Step 'conformance (python)' { & "$venv/python" -m signalforge.conformance --report ../reports/python.json }
    foreach ($gen in Get-ChildItem ../vectors/generators/*.py) {
        Invoke-Step "generator $($gen.BaseName) --check" { & "$venv/python" $gen.FullName --check }
    }
    if (Test-Path ../reports/files) { Remove-Item -Recurse -Force ../reports/files }
    Invoke-Step 'write files (python)' { & "$venv/python" -m signalforge.compare write-files ../reports/files }
}
finally { Pop-Location }

$msbuildJobs = if ($Jobs -gt 0) { @("/m:$Jobs") } else { @() }
$runSettings = if ($Jobs -gt 0) { @('--', "RunConfiguration.MaxCpuCount=$Jobs") } else { @() }
Push-Location (Join-Path $root 'dotnet')
try {
    Invoke-Step 'dotnet build' { dotnet build SignalForge.slnx --nologo -v q $msbuildJobs }
    Invoke-Step 'dotnet test' { dotnet test SignalForge.slnx --no-build --nologo -v q $runSettings }
    Invoke-Step 'dotnet format' { dotnet format SignalForge.slnx --verify-no-changes -v q }
    Invoke-Step 'conformance (dotnet)' { dotnet run --no-build --project tools/SignalForge.Conformance -- --report ../reports/dotnet.json }
    Invoke-Step 'write files (dotnet)' { dotnet run --no-build --project tools/SignalForge.Conformance -- write-files ../reports/files }
    Invoke-Step 'read files (dotnet)' { dotnet run --no-build --project tools/SignalForge.Conformance -- read-files ../reports/files --out ../reports/files-dotnet.json }
    foreach ($cfg in Get-ChildItem (Join-Path $root 'vectors/links') -Filter *.json) {
        Invoke-Step "link $($cfg.BaseName) (dotnet)" { dotnet run --no-build --project tools/SignalForge.Conformance -- link $cfg.FullName --out "../reports/link-$($cfg.BaseName)-dotnet.json" }
    }
}
finally { Pop-Location }

Push-Location (Join-Path $root 'python')
try {
    Invoke-Step 'compare reports' { & "$venv/python" -m signalforge.compare reports ../reports/python.json ../reports/dotnet.json }
    Invoke-Step 'read files (python)' { & "$venv/python" -m signalforge.compare read-files ../reports/files --out ../reports/files-python.json }
    Invoke-Step 'compare files' { & "$venv/python" -m signalforge.compare files ../reports/files-python.json ../reports/files-dotnet.json }
    foreach ($cfg in Get-ChildItem (Join-Path $root 'vectors/links') -Filter *.json) {
        $py, $cs = "../reports/link-$($cfg.BaseName)-python.json", "../reports/link-$($cfg.BaseName)-dotnet.json"
        Invoke-Step "link $($cfg.BaseName) (python)" { & "$venv/python" -m signalforge.compare run-link $cfg.FullName --out $py }
        Invoke-Step "compare link $($cfg.BaseName)" { & "$venv/python" -m signalforge.compare link $py $cs }
    }
}
finally { Pop-Location }

Write-Host "All checks passed: SignalForge $version" -ForegroundColor Green
