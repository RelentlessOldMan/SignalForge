# ADR 0621: Python arrays of real numbers

Status: accepted, 2026-11-26.

## Context

The Python functions that take an array of real numbers checked it with `np.asarray`,
refused complex dtypes, and converted with `astype(np.float64)`. NumPy's conversion accepts
more than numbers. Bools became 0 and 1. Strings and bytes holding digits were parsed.
Dates and time spans became their tick counts. Some inputs failed with the wrong exception:
an int too large for a double raised `OverflowError`, and an object array holding a complex
raised `TypeError`. The review of ADRs 0607–0620 found this, and it was library-wide. C#
takes `ReadOnlySpan<double>` and has no such case.

## Decision

- **One check.** `_checks.real_values(a, what)` converts an array that has already passed
  the complex check:
  - integer, unsigned and floating dtypes convert with `astype(np.float64, copy=False)`, so
    a float64 array is returned as is;
  - an object array converts element by element; each element must be a `numbers.Real`
    that is not a bool and must fit in a double;
  - every other dtype is refused: bool, string, bytes, datetime64, timedelta64, void.
- **Errors.** A refusal raises `ValueError` naming the argument (`invalid_argument`).
- **Where.** The 296 conversions in `measurements.py` and `spectral.py` that followed the
  complex check now call it. The other modules still use `astype` directly; that is the
  next review lead.
- **Bools are not numbers here**, as for scalar arguments (`real`) and counts (`count`).
  A caller with a bool mask converts it on purpose (`mask.astype(float)`).

## Consequences

- Inputs that were refused before are still refused, now always with `ValueError`.
- Inputs that NumPy used to convert quietly (bools, digit strings, dates) are now refused.
  This is a behaviour change, and a deliberate one: those values were almost always a
  mistake by the caller.
- Object arrays are converted by a Python loop, so they are slower than numeric arrays. They
  are rare, and the result is the same.
- `python/tests/test_real_arrays.py` covers eight functions over nine bad inputs and six
  good ones. It failed on 71 of the 72 bad cases before the change. Two mutations were
  checked: letting bools through, and dropping the overflow check. Each failed 8 tests.
