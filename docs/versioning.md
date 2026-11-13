# Versioning

One version for the whole repo: the Python package and the C# library are built, tested and released
together against the same vectors, so they carry the same number.

## The scheme

`YYYY.M.D.N`, for example `2026.11.13.0`.

- `YYYY.M.D` is the local date of the build; `N` counts builds that day, from 0.
- No leading zeros (`2026.1.5.0`, not `2026.01.05.0`). Compare versions numerically, part by part.
- Every build gets a new number. A number is never reused and the version never goes backwards: if
  the stored date is later than today, keep it and bump `N`.
- Valid as is for .NET (`major.minor.build.revision`, each ≤ 65535) and Python (PEP 440). A field that
  takes only three numbers (strict semver) gets `YYYY.M.D-N`.

## Where it lives

| Place | How it gets the version |
|---|---|
| `VERSION` (repo root) | **The source of truth**, committed. `build.ps1` reads it, bumps it and writes it back. |
| .NET assemblies and packages | `dotnet/Directory.Build.props` reads `VERSION` at build time. |
| Python `signalforge.__version__` | Stamped by `build.ps1`; `pyproject.toml` takes it from there (`dynamic = ["version"]`). |

Tests in both languages fail if the stamped values and `VERSION` disagree. Nothing else types a
version by hand.

## Builds, CI and releases

- `build.ps1` is the build: it bumps the version, then runs every check and test in both languages.
  Commit the bumped `VERSION` (and the stamped `__init__.py`) with the work it built.
  `build.ps1 -NoBump` re-runs the checks without making a new version.
- CI builds the committed version and never bumps.
- A release is a build that is published: tag `v<version>` (for example `v2026.11.13.0`) and create a
  GitHub release of the same name. No releases yet.

History: versions before 2026-11-13 were `0.1.0`; the first date version is `2026.11.13.0`.
