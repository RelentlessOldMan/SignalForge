<#
.SYNOPSIS
  Bump the version, then check, build and test both implementations.

.DESCRIPTION
  Every run is a build and gets a new version (docs/versioning.md): VERSION at the repo root is read,
  bumped with Get-NextVersion, written back, and stamped into the Python package. The .NET build
  reads VERSION itself. Then runs, stopping at the first failure:
    Python: ruff check, ruff format --check, mypy, pytest, conformance (report in reports/python.json)
    .NET:   build, test, format --verify-no-changes
  CI does not run this script and never bumps; it builds the committed version.

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
    if ($current -match '^(\d+)\.(\d+)\.(\d+)\.(\d+)$') {
        $y, $m, $d, $n = [int]$Matches[1], [int]$Matches[2], [int]$Matches[3], [int]$Matches[4]
        if ($y * 10000 + $m * 100 + $d -ge $todayKey) {      # same day (or a later date): bump N
            return "$y.$m.$d.$($n + 1)"
        }
    }
    return "$($today.Year).$($today.Month).$($today.Day).0"   # first build today (or no/old-style version)
}

function Invoke-Step([string]$name, [scriptblock]$command) {
    Write-Host "== $name" -ForegroundColor Cyan
    & $command
    if ($LASTEXITCODE -ne 0) { throw "$name failed (exit $LASTEXITCODE)" }
}

# Version: VERSION is the source of truth; the Python package gets a stamped copy.
$versionFile = Join-Path $root 'VERSION'
$current = if (Test-Path $versionFile) { (Get-Content $versionFile -Raw).Trim() } else { $null }
$version = if ($NoBump) { $current } else { Get-NextVersion $current }
if (-not $NoBump) { [IO.File]::WriteAllText($versionFile, "$version`n") }
$init = Join-Path $root 'python/src/signalforge/__init__.py'
$text = Get-Content $init -Raw
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
}
finally { Pop-Location }

$msbuildJobs = if ($Jobs -gt 0) { @("/m:$Jobs") } else { @() }
$runSettings = if ($Jobs -gt 0) { @('--', "RunConfiguration.MaxCpuCount=$Jobs") } else { @() }
Push-Location (Join-Path $root 'dotnet')
try {
    Invoke-Step 'dotnet build' { dotnet build SignalForge.slnx --nologo -v q $msbuildJobs }
    Invoke-Step 'dotnet test' { dotnet test SignalForge.slnx --no-build --nologo -v q $runSettings }
    Invoke-Step 'dotnet format' { dotnet format SignalForge.slnx --verify-no-changes -v q }
}
finally { Pop-Location }

Write-Host "All checks passed: SignalForge $version" -ForegroundColor Green
