# Status

Updated with every chunk of work. Dates are absolute.

## Next

1. **Get a decision on NumPy's bundled libgfortran** (see `docs/dependencies.md` → Open questions).
   Until then NumPy is marked pending.
2. **FFT and spectra ADR**: own FFT in both languages vs Math.NET (C#) / SciPy (Python); windows and
   their normalization; PSD and occupied bandwidth definitions. Conventions written before code.
3. **Phase 3, the QPSK vertical slice**, in both languages with shared vectors:
   root-raised-cosine pulse shaping and matched filter; AWGN at a given Es/N0 (seeded); frequency
   offset; timing and phase recovery (simplest that works); EVM (RMS, %, dB); BER against theory;
   occupied bandwidth; a machine-readable JSON report.
4. **Cross-language compare tool**: C# conformance report (to match the Python
   `--report` output) and a small script that diffs the two reports.

## Built

- 2026-11-12: repo, license (MIT), README, this brain (`CLAUDE.md`, `docs/status.md`), CI.
- 2026-11-12: research and architecture docs: conventions, architecture, testing, dependencies with
  license verification, ADRs 0001–0003.
- 2026-11-12: Python package `signalforge` 0.1.0 and C# library `SignalForge` 0.1.0, each with:
  `Signal` with metadata; units (dB, dBm, Vrms at an impedance); complex and real tones; PRBS
  (O.150 polynomials, orders 7–31); power stats (mean, RMS, peak, PAPR, DC); QPSK Gray map and hard
  demap; bit error count.
- 2026-11-12: shared vectors, 46 cases across units, waveforms, PRBS, measurements and modulation.
  Python 79 passed, 2 skipped (PRBS 23 and 31 full-period checks, too slow); .NET 77 passed.

## Not built

Everything else in the brief: filters, resampling, FFT/spectra, the rest of modulation (PSK/QAM
beyond QPSK, FSK, OFDM, analog), channels and impairments, synchronization, RF measurements (ACPR,
SFDR, phase noise, NF), standards waveforms, file formats (SigMF, WAV, raw IQ), plotting, CLI,
packaging and publishing.

## Lessons

- 2026-11-12: Check build tools' licenses too: hatchling and mypy both pull in pathspec (MPL-2.0).
  flit_core is clean.
- 2026-11-12: Binary wheels can bundle libraries under other licenses; read the wheel's own
  `LICENSE.txt`, not just the project's top-level license.
- 2026-11-12: The `dotnet new xunit` template is xunit v2; there is no `xunit3` template in the SDK.
- 2026-11-12: Avoid long bash heredocs with quotes in JSON or C#; write such files directly.
