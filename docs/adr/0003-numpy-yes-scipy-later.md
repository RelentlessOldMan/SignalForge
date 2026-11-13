# 0003: Python builds on NumPy; SciPy waits for a need; C# starts with the base library only

Date: 2026-11-12. Status: accepted, NumPy approval pending (see `docs/dependencies.md`).

## Decision

- Python: NumPy is the array type and the only runtime dependency. SciPy comes in when filter design
  or resampling need it, after the same license check.
- C#: no runtime packages yet. The first FFT decision (Math.NET Numerics vs. FftSharp vs. our own
  radix-2/Bluestein) is made when the DSP module starts, recorded as its own ADR.
- Build and test tools are held to the same license rule: flit_core instead of hatchling, no mypy
  (both pull in MPL-2.0 pathspec).
