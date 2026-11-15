# ADR 0090: Integer `.npy` dtypes on read

Status: accepted, 2026-11-14

## Context

`read_npy` ([ADR 0056](0056-npy.md), [ADR 0088](0088-npy-read-dtypes.md)) reads only floating-point
descrs. Counts, indices, bit streams, symbol decisions and raw ADC codes are often saved as NumPy
integer arrays. ADR 0088 kept them out because WAV and SigMF integers are scaled to full scale, and a
`.npy` file has no full-scale convention to scale by.

## Decision

- **`read_npy` (and so `read_npz`) accepts** the integer descrs `'|i1'`, `'|u1'`, and `'<'` or
  `'>'` with `i2`, `u2`, `i4`, `u4`, `i8` or `u8`: two's-complement signed or unsigned integers
  of that many bytes, in that byte order. A one-byte item has no byte order, so its descr must use
  `|`, the only form NumPy writes; `'<i1'`, `'>u1'` and `'=i2'` are rejected.
- **No scaling**: each integer becomes the `float64` (C# `double`) with the same value. Unlike
  WAV and SigMF, a `.npy` file says nothing about full scale, so code that wants one divides by it
  itself.
- **Exactness**: every integer of at most 32 bits, and every 64-bit one up to 2^53 in magnitude, is
  exact. A wider 64-bit value rounds to the nearest double, ties to even, as `float(int)`,
  `numpy.astype(np.float64)` and C#'s `(double)long` / `(double)ulong` all do. Reading never fails
  on such a value.
- **Integer files are real**: C#'s `ReadNpy<Complex>` rejects them, as it rejects a real float file.
- **`write_npy` is unchanged**: it writes only `'<f8'` and `'<c16'`.
- **Expected values**: the npy generator packs the integers with `struct` (`b`, `B`, `h`, `H`, `i`,
  `I`, `q`, `Q`, both byte orders), and the expected doubles are the integers themselves, or for
  values beyond 2^53 the double worked out by hand from the binary expansion and the tie rule.

## Consequences

- An integer file read and written back becomes a `'<f8'` file; that loses nothing for values up to
  2^53.
- Boolean (`'|b1'`), structured and other dtypes stay rejected.
