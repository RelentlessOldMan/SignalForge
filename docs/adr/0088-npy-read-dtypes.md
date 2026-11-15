# ADR 0088: More `.npy` dtypes on read

Status: accepted, 2026-11-14

## Context

`read_npy` ([ADR 0056](0056-npy.md)) reads only `'<f8'` and `'<c16'`. Arrays saved from receivers,
GPUs and machine-learning code are often `float32` or `complex64`, sometimes `float16`, and a file
saved on a big-endian machine, or from an array with a `'>'` dtype, has `'>'` in its descr. Each of
these can be widened to binary64 without losing anything, so they can be read without a
lossy-conversion option.

## Decision

- **`read_npy` accepts** the descrs `'<f8'`, `'>f8'`, `'<f4'`, `'>f4'`, `'<f2'`, `'>f2'` (real) and
  `'<c16'`, `'>c16'`, `'<c8'`, `'>c8'` (complex: real then imaginary part, each of half the item
  size). The byte-order character must be `<` or `>`: `=` and `|` are rejected, because a file
  never needs them for these types and `=` would make the file's meaning depend on the reader.
- **Values are widened exactly** to `float64` / `complex128` (C# `double` / `Complex`), the same
  widening as `f32` and `f16` SigMF samples. ±inf, ±0 and subnormals keep their values; a NaN stays
  NaN, with no promise about its payload.
- **`write_npy` is unchanged**: it writes only `'<f8'` and `'<c16'`, which lose nothing.
- **Data size**: the data must be exactly `n` times the item size (2, 4, 8 or 16 bytes).
- **Expected values**: the npy generator packs the data with `struct` (`e`, `f`, `d`, both byte
  orders) from values each narrow type holds exactly (dyadic rationals within range), so the
  expected doubles are the values themselves.

## Consequences

- C#'s `ReadNpy<double>` still rejects a complex file, and `ReadNpy<Complex>` a real one, whatever
  the width.
- Integer dtypes stay rejected: they need a scaling decision that the file does not carry.
