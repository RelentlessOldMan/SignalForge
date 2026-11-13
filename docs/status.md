# Status

Updated with every chunk of work. Dates are absolute.

## Next

1. **Phase 3, the rest of the QPSK slice**, in both languages: timing and phase recovery (simplest
   that works: a data-aided or Gardner timing estimate and a fourth-power phase/frequency
   estimate), then an end-to-end link function that runs bits → shaping → channel → recovery →
   EVM/BER and returns a machine-readable JSON report.
2. **Cross-language compare tool**: C# conformance report (to match the Python
   `--report` output) and a small script that diffs the two reports.

## Built

- 2026-11-12: repo, license (MIT), README, this brain (`CLAUDE.md`, `docs/status.md`), CI.
- 2026-11-12: research and architecture docs: conventions, architecture, testing, dependencies with
  license verification, ADRs 0001–0005 (0006 below).
- 2026-11-12: Python package `signalforge` and C# library `SignalForge` (then 0.1.0), each with:
  `Signal` with metadata; units (dB, dBm, Vrms at an impedance); complex and real tones; PRBS
  (O.150 polynomials, orders 7–31); power stats (mean, RMS, peak, PAPR, DC); QPSK Gray map and hard
  demap; bit error count.
- 2026-11-12: NumPy approved as the Python runtime dependency; its bundled GCC Fortran runtime
  (GCC runtime exception) puts no obligation on our code. ADR 0004.
- 2026-11-12: PSF-2.0 approved, MPL-2.0 allowed for dev-only tools (ADR 0005); mypy strict added to
  the Python checks and CI, tests annotated.
- 2026-11-12: shared vectors, 46 cases across units, waveforms, PRBS, measurements and modulation.
  Python 79 passed, 2 skipped (PRBS 23 and 31 full-period checks, too slow); .NET 77 passed.
- 2026-11-13: spectral module in both languages (ADR 0006): FFT (Python `numpy.fft`; C# its own
  radix-2 plus Bluestein, no dependency), frequency axes, seven windows with coherent gain and ENBW,
  Welch PSD (one- and two-sided), occupied bandwidth (β/2), channel power. 59 new vectors (105 in
  all). Python 153 passed, 2 skipped (CI: Python 3.10 and 3.13); .NET 148 passed.
- 2026-11-13: date-based versioning (`YYYY.M.D.N`, docs/versioning.md): `VERSION` at the root is the
  one source; .NET reads it at build time, `build.ps1` bumps it and stamps Python's `__version__`;
  tests in both languages check they agree. Was 0.1.0; first build 2026.11.13.0. Python 155 passed,
  2 skipped; .NET 149 passed.
- 2026-11-13: review and fixes across both languages:
  - **Bugs fixed:** occupied bandwidth could return `inf` at fraction 1 when trailing bins were zero
    (the total and the running sum differed in the last bit); a one-sided PSD undercounted DC and
    Nyquist power. New `span` argument for OBW and channel power, and `SpectralDensity.span`
    `(0, fs/2)` for one-sided PSDs (conventions: Bins as rectangles).
  - **Stricter arguments:** Kaiser β limited to 0…700 (I₀ overflows above 713); Welch takes `beta`;
    sample rates and impedances must be finite; `power_stats` and PSD frequencies reject NaN and
    infinity; QPSK bits must be exactly 0 or 1; Python counts must be integers (`3.0` is
    rejected). New conventions section: Arguments.
  - **Conformance runners:** the C# runner passed some broken cases (an argument it didn't read,
    a decoding error counted as the expected `invalid_argument`, truncated `re`/`im` pairs,
    approximate window names). Both runners now reject unknown arguments and compare types
    strictly. `vectors/selftest/must_fail.json` holds 11 wrong cases both runners must fail; it
    found one more crash in the C# runner.
  - 26 new vectors (131 in all): span cases, the fraction-1 regression, Kaiser and Welch β,
    non-finite inputs, PRBS 11/15/20/23/31 prefixes and a PRBS7 run past its period.
  - Docs and tooling: build.ps1 refuses a missing or malformed `VERSION`; CI actions updated to the
    current node24 majors; NumPy floor raised to 2.2 (the oldest version CI tests); README in the
    REPO-SETUP form; NuGet metadata. Two license questions are open for the user (dependencies.md):
    libquadmath (LGPL) in NumPy's Linux wheels, and NumPy's vendored permissive parts.
  - Python 207 passed, 2 skipped; .NET 189 passed.
- 2026-11-13: QPSK link building blocks in both languages (ADR 0007): modules `dsp` (convolution,
  upsampling, unit-energy RRC taps, pulse shaping) and `channel` (seeded AWGN at Es/N0, frequency
  offset); in `metrics`, EVM (RMS, %, dB, peak) and QPSK BER theory, with C#'s own erfc. 49 new
  vectors (180 in all); RRC expected values come from the inverse Fourier transform of the
  root-raised-cosine spectrum (Gauss–Legendre), not the closed form. Unit tests check AWGN
  statistics, the matched filter's Nyquist property, and a shaped QPSK link's BER against theory
  at 4 dB Eb/N0 in both languages. Python 278 passed, 2 skipped; .NET 259 passed.
- 2026-11-13: review of the link blocks. Python raised `OverflowError` (not `ValueError`) for an
  extreme Es/N0 or Eb/N0, where C# quietly returned infinity: AWGN now rejects an Es/N0 so low the
  noise variance overflows (both languages), and BER theory returns 0 above about 3080 dB. CI's
  Python 3.10 mypy (NumPy 2.2 stubs) failed on two annotations; fixed and checked locally on 3.10.
  2 new vectors (182). Python 283 passed, 2 skipped (also on 3.10); .NET 261 passed.

## Not built

Everything else in the brief: filter design (FIR/IIR beyond RRC), resampling, spectrograms and spectral options beyond Welch
(zero padding, detrending, median averaging), the rest of modulation (PSK/QAM
beyond QPSK, FSK, OFDM, analog), impairments beyond AWGN and frequency offset, synchronization, RF measurements (ACPR,
SFDR, phase noise, NF), standards waveforms, file formats (SigMF, WAV, raw IQ), plotting, CLI,
packaging and publishing.

## Lessons

- 2026-11-12: The test for any dependency is whether it could ever force our code under the GPL or
  limit commercial shipping. A GPL label on a compiler runtime with the GCC exception does not.
- 2026-11-12: Check build tools' licenses too: hatchling and mypy both pull in pathspec (MPL-2.0).
  flit_core is clean. Whether a tool is shipped decides which licenses it may use (ADR 0005).
- 2026-11-12: NumPy's type stubs differ by version: Python 3.10 gets NumPy 2.2, which rejects a bare
  `np.ndarray` under strict mypy. Annotate with `NDArray[dtype]` and run mypy on both Pythons.
- 2026-11-12: Binary wheels can bundle libraries under other licenses; read the wheel's own
  `LICENSE.txt`, not just the project's top-level license.
- 2026-11-12: The `dotnet new xunit` template is xunit v2; there is no `xunit3` template in the SDK.
- 2026-11-12: Avoid long bash heredocs with quotes in JSON or C#; write such files directly.
- 2026-11-13: Windows PowerShell 5.1 splits a splatted `-m:1` into `- m : 1` for native commands;
  pass MSBuild switches as `/m:1`. Git Bash does the opposite: it turns `/m:1` into a path, so
  type `-m:1` there.
- 2026-11-13: Git Bash mangles backslash paths passed through `cmd /c`; run cmd invocations from
  the PowerShell tool instead.
- 2026-11-13: A conformance runner needs its own tests. Hand-written wrong cases
  (`vectors/selftest`) caught a C# runner that passed cases it never really ran.
- 2026-11-13: NumPy wheels bundle different native libraries per platform (Linux ships
  libquadmath, Windows doesn't). Check the wheels for every platform CI or users install, not
  only the local one.
- 2026-11-13: For a special function, check relative error over the whole range against the C
  library before trusting it. The naive `exp(-x*x)` in erfc costs about 1e-13 near x = 25 from
  the rounding of x²; splitting x into a short `z` plus a remainder fixes it. Below about 1e-308
  results are subnormal and relative error stops meaning anything.
