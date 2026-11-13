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
      "args": {"x": 1000},
      "expected": 30.0,
      "tol": {"abs": 1e-12, "rel": 1e-12},
      "source": "10*log10(1000) = 30"
    }
  ]
}
```

- `id`: unique within the file. `op`: the operation, by its Python name. `args`: named arguments,
  Python names; omitted arguments take the function's documented default.
- `expected`: the result. A case expecting an error has `"error": "invalid_argument"` instead
  (`ValueError` in Python, `ArgumentException` or a subclass in C#).
- `tol`: optional. Passes when `|actual − expected| ≤ abs + rel·|expected|`. Defaults: `abs` 1e-12,
  `rel` 1e-12. For complex values the difference is the complex modulus.
- `source`: required. How the expected value was obtained.
- Records compare only the fields listed in `expected`; booleans compare exactly. Enumerated choices
  (such as a window name) are strings in their Python spelling (`"blackman_harris"`); the C# runner
  maps them to its enum.

### Values

| JSON | Meaning |
|---|---|
| number | real number (integers compare as numbers) |
| `"inf"`, `"-inf"`, `"nan"` | special floats; NaN matches only NaN |
| `[1, 2, 3]` | real or integer array |
| `{"re": 1, "im": 2}` | complex number |
| `{"re": [..], "im": [..]}` | complex array |
| any other object | a structured result; **only the fields listed are compared** |

Structured results use the Python field names (`mean_power`, `peak_index`, …).
