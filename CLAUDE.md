# SignalForge: notes for every session

Read this first, then [docs/status.md](docs/status.md) for what is built and what is next.

## The brain: what goes in it and what stays private

This file and `docs/status.md` are the project's memory. Anything a future session needs to know
goes here, in the repo, so it travels with the code.

- Update `docs/status.md` with every chunk of work, **in the same commit** as the work.
- Update this file when a rule changes. If a rule only lives in private memory, move it here.
- Push when a chunk is done.
- Never put machine names, IP addresses, user names, local paths, credentials, or rules about how one
  particular machine schedules its jobs into the repo. Facts about a job's own needs (how long it
  takes, how much memory it uses) are fine.

## What the project is for

A signal generation, DSP and measurement framework, built twice: Python (`python/`) and C#/.NET
(`dotnet/`). The two have **no runtime dependency on each other**. They share conventions
(`docs/conventions.md`) and test vectors (`vectors/`), and must agree numerically.

The original brief is `docs/brief.md`. It was a starting idea, not a hard spec: where it and the
repo docs disagree, the repo docs win.

## Working through a plan

- Work in vertical slices: a feature is done when it exists in **both** languages, has shared
  vectors, and both suites pass. Don't let one language run ahead by more than a slice.
- Order of work is in `docs/status.md` → Next. Take the top item unless the user says otherwise.
- A decision that is hard to reverse (a dependency, a public API shape, a convention) gets an ADR in
  `docs/adr/`, numbered in order.
- Run the builds and tests and report the actual results. Don't claim something passes without
  having run it.

## Code rules

- **Licenses are strict.** SignalForge must always be shippable commercially under MIT with no
  restrictions; nothing may ever require our code to be GPL or otherwise copyleft. Only MIT,
  BSD-2-Clause, BSD-3-Clause, Apache-2.0 and ISC, including transitive dependencies and build
  tools; PSF-2.0 too; MPL-2.0 only for dev tools that are never shipped. Anything else needs the
  user's explicit approval first; approvals are listed in `docs/dependencies.md`.
  Check the license from the package's own metadata or license file, and record every dependency in
  `docs/dependencies.md` with how it was checked. Don't copy code or text from projects with other
  licenses (the SigMF spec is CC-BY-SA: implement from the description, don't copy it).
- **Expected values come from outside SignalForge**: an analytical result, a hand derivation, or an
  independent reference. Never generate a vector from SignalForge's own output and call it expected.
  Each vector case says where its value came from in `source`.
- **Conventions first.** Anything two implementations could define differently (scaling, dB, bit
  order, sign, window normalization) is written in `docs/conventions.md` before it is coded.
- Names match across languages: `snake_case` in Python, `PascalCase` in C#, same meaning. A vector
  `op` is the Python name; the C# runner maps it.
- Python: NumPy is the only runtime dependency. Type hints on public functions. `ruff check` and
  `ruff format` clean (line length 100). `mypy` clean (strict, `src` and `tests`).
- C#: no package dependencies in the library. Warnings are errors, analyzers at latest-recommended,
  XML docs on every public member, `dotnet format` clean.
- Bad arguments raise `ValueError` (Python) or `ArgumentException` and subclasses (C#); vectors call
  this `invalid_argument`.
- Random streams differ between languages. Cross-language checks on noisy signals compare
  statistics, or exchange the samples as files.

## Git

- Branch `main`, remote `origin` = github.com/RelentlessOldMan/SignalForge.
- Commit each finished chunk with `docs/status.md` updated in the same commit, then push.
- The repo doesn't take issues or pull requests (see README).

## Versioning

One date-based version for the whole repo, `YYYY.M.D.N`, in `VERSION` at the root: see
[docs/versioning.md](docs/versioning.md). `build.ps1` is the build: every run bumps the version, then
runs every check below in both languages. Commit the bumped `VERSION` and the stamped
`python/src/signalforge/__init__.py` with the work they built. Never type a version anywhere else;
CI never bumps.

## Commands

The build, from the repo root: `./build.ps1` (Windows PowerShell or pwsh; `-Jobs N` limits .NET
parallelism, `-NoBump` re-runs without a new version). The Python venv lives at `.venv` in the repo
root (gitignored). Setup, then the steps `build.ps1` runs, one by one, from the repo root:

```
python -m venv .venv
.venv/Scripts/pip install -e python[dev]        # bin/ instead of Scripts/ on Linux and macOS

cd python
../.venv/Scripts/ruff check . && ../.venv/Scripts/ruff format --check .
../.venv/Scripts/mypy
../.venv/Scripts/pytest -q
../.venv/Scripts/python -m signalforge.conformance --report ../reports/python.json

cd ../dotnet
dotnet build SignalForge.slnx
dotnet test SignalForge.slnx
dotnet format SignalForge.slnx --verify-no-changes
dotnet run --no-build --project tools/SignalForge.Conformance -- --report ../reports/dotnet.json

cd ../python
../.venv/Scripts/python -m signalforge.compare reports ../reports/python.json ../reports/dotnet.json
```

`build.ps1` runs all of this, plus every vector generator's `--check` (as CI does) and the link
configs in `vectors/links/` in both languages.

### Job sizes

Measured 2026-11-13:

- Python `pytest` (1088 tests): about 5 s.
- .NET `dotnet test` (incremental build + 877 tests): about 6 s.
- `vectors/generators/fir.py`: about 3 s; `resample.py`: well under 1 s.
- `build.ps1 -Jobs 1` (everything, incremental): about 20 s before the cross-language steps were
  added; not re-timed since. A clean build with restore takes
  longer (not yet timed).

Memory not measured yet; nothing holds more than a few MB of samples. No job uses the GPU.

## Where things are

| Path | What |
|---|---|
| `docs/status.md` | Next, built, not built, lessons. |
| `docs/conventions.md` | Numerical conventions both languages follow. |
| `docs/architecture.md` | Modules, the signal type, measurement results, naming. |
| `docs/dependencies.md` | Every dependency, its license and how it was checked; rejected list; open questions. |
| `docs/testing.md` | Test layers, where expected values come from, tolerances. |
| `docs/versioning.md`, `VERSION`, `build.ps1` | Version scheme, the version, the build. |
| `docs/adr/` | Architecture decision records. |
| `vectors/README.md`, `vectors/cases/` | Shared vector format and cases. |
| `vectors/generators/` | Stdlib-only scripts that compute vector files from first principles. |
| `vectors/selftest/` | Deliberately wrong cases both runners must fail. |
| `vectors/files/` | SigMF recordings the `read_sigmf` vectors read (written by `generators/files.py`). |
| `vectors/links/` | `qpsk_link` configs run in both languages and compared. |
| `python/src/signalforge/compare.py` | Cross-language compare: conformance reports, link reports. |
| `dotnet/tools/SignalForge.Conformance/` | C# conformance report and link runner (command line). |
| `python/src/signalforge/` | Python package; `conformance.py` runs the vectors. |
| `dotnet/src/SignalForge/` | C# library. |
| `dotnet/tests/SignalForge.Tests/` | C# tests; `Conformance.cs` runs the vectors. |
| `.github/workflows/ci.yml` | CI: lint and test both languages, then compare them. |
