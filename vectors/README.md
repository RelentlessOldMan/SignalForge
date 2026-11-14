# Shared test vectors

Language-neutral cases that both implementations must pass. The Python test suite and the .NET test
suite each load every `cases/*.json` file and run every case. Rules for where expected values may
come from are in [docs/testing.md](../docs/testing.md): never from SignalForge's own output.

## File format (schema 1)

```json
{
  "schema": 1,
  "suite": "units",
  "description": "what the file covers",
  "cases": [
    {
      "id": "lin_to_db.1000",
      "op": "lin_to_db",
      "args": {"ratio": 1000},
      "expected": 30.0,
      "tol": {"abs": 1e-12, "rel": 1e-12},
      "source": "10*log10(1000) = 30"
    }
  ]
}
```

- `id`: unique within the file. `op`: the operation, by its Python name. `args`: named arguments,
  Python names; omitted arguments take the function's documented default. An argument the function
  does not take fails the case (so a misspelling cannot silently fall back to a default).
- `expected`: the result. A case expecting an error has `"error": "invalid_argument"` instead
  (`ValueError` in Python, `ArgumentException` or a subclass in C#).
- `tol`: optional. Passes when `|actual − expected| ≤ abs + rel·|expected|`. Defaults: `abs` 1e-12,
  `rel` 1e-12. For complex values the difference is the complex modulus.
- `source`: required. How the expected value was obtained.
- Comparison is type-strict: a real array never matches a complex result, a scalar never matches
  a one-element array, and a boolean matches only a boolean. Integer and bit arrays compare as real
  arrays.
- Records compare only the fields listed in `expected`; booleans compare exactly. Enumerated choices
  (such as a window name) are strings in their Python spelling (`"blackman_harris"`); the C# runner
  maps them to its enum.

### Values

| JSON | Meaning |
|---|---|
| number | real number (integers compare as numbers) |
| `"inf"`, `"-inf"`, `"nan"` | special floats; NaN matches only NaN |
| `null` | no value (`None` / `null`); matches only null |
| `[1, 2, 3]` | real or integer array |
| `{"re": 1, "im": 2}` | complex number |
| `{"re": [..], "im": [..]}` | complex array |
| any other object | a structured result; **only the fields listed are compared** |

Structured results use the Python field names (`mean_power`, `peak_index`, …).

## Generators

`generators/*.py` compute a whole case file from first principles with the Python standard
library only (`fir.py` writes `cases/fir.json`, `resample.py` writes `cases/resample.json`, `error_rates.py` writes `cases/error_rates.json`, `fractional_delay.py` writes `cases/fractional_delay.json`, `timing_loop.py` writes `cases/timing_loop.json`, `carrier_loop.py` writes `cases/carrier_loop.json`, `clock_offset.py` writes `cases/clock_offset.json`, `spectrogram.py` writes `cases/spectrogram.json`, `iir.py` writes `cases/iir.json`, `equiripple.py` writes `cases/equiripple.json`, `group_delay.py` writes `cases/group_delay.json`, `least_squares.py` writes `cases/least_squares.json`, `welch.py` writes `cases/welch.json`, `lomb_scargle.py` writes `cases/lomb_scargle.json`, `stimuli.py` writes `cases/stimuli.json`, `tone_metrics.py` writes `cases/tone_metrics.json`, `files.py` writes `cases/files.json` and the
recordings in `files/`, `fsk.py` writes `cases/fsk.json`, `wav.py` writes `cases/wav.json` and the
`.wav` files in `files/`, `npy.py` writes `cases/npy.json` and the `.npy` files in `files/`). Run one from the repo root to rewrite its file;
`--check` compares instead and exits 1 on any difference. CI runs every generator with `--check`.

## Link configs

`links/*.json` are `qpsk_link` configs (the config's field names) that `build.ps1` and CI run in
both languages and compare statistically (`docs/testing.md`, Cross-language checks). They have no
expected values.

## Runner self-test

`selftest/must_fail.json` holds deliberately wrong cases (a wrong value, a misspelled or missing
argument, a type mismatch, ragged complex arrays, an unknown op, …). Both test suites run them and
require every one to **fail**: a runner that passes any of them would also pass a broken vector.
These are not conformance cases and the conformance report ignores them.
