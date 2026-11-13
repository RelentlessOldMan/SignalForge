# Status

Updated with every chunk of work. Dates are absolute.

## Next

1. **Phase 3, the QPSK vertical slice**, in both languages with shared vectors:
   root-raised-cosine pulse shaping and matched filter; AWGN at a given Es/N0 (seeded); frequency
   offset; timing and phase recovery (simplest that works); EVM (RMS, %, dB); BER against theory;
   occupied bandwidth (now available); a machine-readable JSON report.
2. **Cross-language compare tool**: C# conformance report (to match the Python
   `--report` output) and a small script that diffs the two reports.

## Built

- 2026-11-12: repo, license (MIT), README, this brain (`CLAUDE.md`, `docs/status.md`), CI.
- 2026-11-12: research and architecture docs: conventions, architecture, testing, dependencies with
  license verification, ADRs 0001–0005 (0006 below).
- 2026-11-12: Python package `signalforge` 0.1.0 and C# library `SignalForge` 0.1.0, each with:
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
  all). Python 153 passed, 2 skipped (mypy clean on 3.10 and 3.12); .NET 148 passed.

## Not built

Everything else in the brief: filters, resampling, spectrograms and spectral options beyond Welch
(zero padding, detrending, median averaging), the rest of modulation (PSK/QAM
beyond QPSK, FSK, OFDM, analog), channels and impairments, synchronization, RF measurements (ACPR,
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
- 2026-11-13: Git Bash mangles backslash paths passed through `cmd /c`; run cmd invocations from
  the PowerShell tool instead.
- 2026-11-12: Avoid long bash heredocs with quotes in JSON or C#; write such files directly.
