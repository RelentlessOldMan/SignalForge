# Dependencies and licenses

SignalForge may only depend on software under MIT, BSD-2-Clause, BSD-3-Clause, Apache-2.0 or ISC.
Anything else, including other permissive licenses (PSF-2.0, Zlib, 0BSD, CC0, Unlicense), needs the
user's explicit approval, recorded below with a date. Copyleft and reciprocal licenses (GPL, LGPL,
AGPL, MPL, EPL, CDDL, SSPL), source-available licenses and unlicensed code are not allowed. The rule
covers runtime, build, test, native, transitive, optional and copied code alike.

The point of the rule: **SignalForge must always be shippable commercially, under MIT, with no
restrictions. Nothing we use may ever require any SignalForge code to be licensed under the GPL or
any other copyleft license.** A dependency that fails this is used only as a test reference, if at
all.

## How a dependency gets approved

1. Read the license from an authoritative source: the license file in the source repository or the
   distributed package (wheel `dist-info/licenses`, NuGet `.nuspec` `<license>`), not a package
   index's summary line.
2. List its transitive dependencies for the platforms we ship on and check each one the same way.
3. Check what it **bundles**: wheels and NuGet packages often ship native libraries under licenses of
   their own (see NumPy below).
4. Note attribution or NOTICE obligations (Apache-2.0 NOTICE files must be carried).
5. Add a row to the inventory with version, source, license, how it was verified and the date. A
   candidate whose license cannot be verified is **rejected** until it can.

## Inventory (in use)

Verified 2026-11-12 against the installed packages' own metadata, plus the GitHub license API for
the source repositories.

### Python

| Package | Version | Use | License | Verified from | Notes |
|---|---|---|---|---|---|
| numpy | 2.5.4 | runtime | BSD-3-Clause (+ 0BSD, MIT, Zlib, CC0-1.0 for vendored parts) | wheel `License-Expression`, `dist-info/licenses/` | Approved 2026-11-12 ([ADR 0004](adr/0004-numpy-gcc-runtime-exception.md)). Wheels bundle the GCC Fortran runtime under GPL-3.0-or-later WITH GCC-exception-3.1; no obligation on our code. Bundled distributions must carry NumPy's `LICENSE.txt`. |
| flit_core | 4.2.0 | build backend | BSD-3-Clause | wheel metadata | no dependencies |
| pytest | 9.2.0 | test | MIT | wheel metadata | |
| ↳ iniconfig | 2.3.1 | test (transitive) | MIT | wheel metadata | |
| ↳ packaging | 26.3 | test (transitive) | Apache-2.0 OR BSD-2-Clause | wheel metadata | |
| ↳ pluggy | 1.7.0 | test (transitive) | MIT | wheel metadata | |
| ↳ pygments | 2.21.0 | test (transitive) | BSD-2-Clause | wheel metadata | |
| ↳ colorama | 0.4.6 | test (transitive, Windows) | BSD-3-Clause | classifier + upstream LICENSE | |
| ruff | 0.17.5 | lint/format | MIT | wheel metadata | single binary, no Python deps |

### .NET

| Package | Version | Use | License | Verified from |
|---|---|---|---|---|
| (none) | | runtime | | The library uses only the .NET base class library (MIT). |
| Microsoft.NET.Test.Sdk | 17.14.1 | test | MIT | `.nuspec` |
| ↳ Microsoft.TestPlatform.ObjectModel / TestHost | 17.14.1 | test (transitive) | MIT | `.nuspec` |
| ↳ Microsoft.CodeCoverage | 17.14.1 | test (transitive) | MIT | `.nuspec` |
| ↳ Newtonsoft.Json | 13.0.3 | test (transitive) | MIT | `.nuspec` |
| xunit (+ .core, .assert, .abstractions, .analyzers, .extensibility.*) | 2.9.3 | test | Apache-2.0 | `.nuspec`; `.abstractions` 2.0.3 points at the xunit license file (Apache-2.0) |
| xunit.runner.visualstudio | 3.1.4 | test | Apache-2.0 | `.nuspec` |

xunit is Apache-2.0 and is only used by the test project; nothing from it is redistributed with the
library, so no NOTICE file is needed today. Revisit if a test artifact is ever shipped.

### CI

GitHub Actions `actions/checkout`, `actions/setup-python` and `actions/setup-dotnet` are MIT. They run
on GitHub's runners and are not distributed.

## Rejected

| Candidate | Why |
|---|---|
| mypy 2.4.1 | Depends on **pathspec** (MPL-2.0) and **typing_extensions** (PSF-2.0). No Python type checker in CI until a clean option is approved. Type hints are still written. |
| hatchling | Depends on pathspec (MPL-2.0). flit_core is used instead. |
| sigmf-python | LGPL-3.0. SigMF support will be written from the format description. |
| FFTW | GPL-2.0 (commercial licence sold separately). |

The SigMF *specification* repository is CC-BY-SA-4.0. Implementing a file format from its description
is fine; **copying the spec's text or schema files into this repo is not**, because CC-BY-SA is
share-alike.

## Candidates, not yet adopted

Researched 2026-11-12. None is in use; each needs the full check above before it is.

| Candidate | Lang | Capabilities | License (repo) | Status / plan |
|---|---|---|---|---|
| SciPy | Py | filter design, resampling, windows, spectral estimation, special functions | BSD-3-Clause | Strong candidate for `signal` and `fft`. Its wheels bundle OpenBLAS and libgfortran like NumPy's, so it gets the same check as NumPy (ADR 0004). Also useful as an **independent reference** in tests. |
| Math.NET Numerics | C# | FFT, linear algebra, statistics, interpolation, some filtering | MIT | Candidate for FFT and linear algebra. Last pushed 2025-03: mature but slow-moving. Check the managed provider only; the optional MKL/OpenBLAS native providers are separate packages with their own licenses. |
| FftSharp | C# | FFT, windows, PSD helpers | MIT | Small and simple; less general than Math.NET. Fallback if Math.NET's FFT is unsuitable. |
| NWaves | C# | filters, filter design, resampling, windows, audio-oriented DSP | MIT | Last pushed 2022-09: unmaintained. Mine for ideas and test comparisons; do not depend on it. |
| KISS FFT | C | small mixed-radix FFT | BSD-3-Clause (SPDX header in COPYING) | Only if a native FFT is ever needed. |
| scikit-dsp-comm | Py | comms helpers: pulse shaping, synchronizers, BER sims | BSD-2-Clause | Depends on matplotlib (PSF-based license) and scipy. Use as an **independent reference** in tests only, if approved. |
| CommPy | Py | modulation, channel coding, channels | BSD-3-Clause | Last pushed 2023-05. Reference only. |

## Approvals

Licenses and cases outside the allowed list that the user has approved.

| Date | What | Scope | Record |
|---|---|---|---|
| 2026-11-12 | GCC runtime (GPL-3.0-or-later WITH GCC-exception-3.1) bundled inside NumPy's wheels | NumPy as a runtime dependency only; not a general approval of GPL code | [ADR 0004](adr/0004-numpy-gcc-runtime-exception.md) |

## Open questions for the user

1. **PSF-2.0** (typing_extensions) is permissive but not on the list. Approving it would let mypy in,
   except mypy also needs pathspec (MPL-2.0), so mypy stays out regardless.
