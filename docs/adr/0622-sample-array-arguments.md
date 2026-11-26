# ADR 0622: Python arrays of samples, and the rest of the real arrays

Status: accepted, 2026-11-26.

## Context

ADR 0621 sent the real-array conversions in `measurements` and `spectral` through
`_checks.real_values`, but only where they followed the "must be real" check. 17 more
conversions turned user arguments into float64 with a bare `astype`. Probes confirmed that
`Signal`, `iq_imbalance` and `analytic_signal` took bools, digit strings and time spans as
numbers, and raised `OverflowError` for huge ints. `Signal` and `iq_imbalance` take complex
samples too, so they need a check that lets complex values through.

## Decision

- **Real arrays.** The 15 remaining argument conversions call `real_values`:
  - `measurements`: `gcc_phat`, `energy_separation`, `decay_time`, `iacc`,
    `lateral_fraction`, the `frequencies` of `modulation_transfer`, and the band times of
    `bass_ratio` and `treble_ratio`;
  - `spectral`: `psd_confidence_interval`, `coherence_confidence_interval`, `mfcc` (both
    arrays), `delta`, `analytic_signal`.
- **Sample arrays.** A new `_checks.sample_values(a, what)` serves arrays that may be complex:
  - floating and complex dtypes pass as they are, so `Signal` keeps a float32 or complex64
    array's dtype as before;
  - integer and unsigned dtypes become float64;
  - an object array converts element by element: each element must be a `numbers.Number`
    that is not a bool and fits in a double; the result is complex128 if any element is
    complex, else float64;
  - every other dtype is refused.

  `Signal` and `iq_imbalance` use it.
- **Errors.** A refusal raises `ValueError` saying the argument "must be numbers" (or "real
  numbers"), which is `invalid_argument`.
- **Left alone.** The other `astype(np.float64)` calls convert values SignalForge made
  itself (bin counts, ranks, index ranges, waveform levels), bits already checked by the
  modulation mappers, frequency arrays already checked for kind `iuf`, or file data whose
  dtype the reader has already fixed.

## Consequences

- No array argument in the Python library takes bools, strings, bytes, dates or times as
  numbers any more.
- `real_values` converts with `copy=False`, where the old `astype` copied. None of the 15
  functions writes to the array after converting it, so caller data is not changed.
- `python/tests/test_numeric_arrays.py` derives each bad input from a working input of the
  right shape. It requires the message to name numbers, so a later shape or value check
  cannot pass it by accident. All 169 bad cases failed before the change. Two mutations were
  checked: letting bools through, and skipping the element check. They failed 2 and 4 tests.
