# ADR 0087: Half-precision SigMF samples

Status: accepted, 2026-11-14

## Context

SigMF names `f16` among its sample types, and some receivers and machine-learning datasets store
IQ as binary16 to halve the size of `f32`. SignalForge rejected it
([ADR 0012](0012-signal-files.md), [ADR 0058](0058-unsigned-sample-types.md)). Both languages
have the type built in: NumPy's `float16` and .NET's `Half`. Neither is a new dependency.

## Decision

- **`rf16_le`, `rf16_be`, `cf16_le`, `cf16_be`** are accepted by `encode_samples`,
  `decode_samples`, `write_sigmf` and `read_sigmf`. They are IEEE 754 binary16 in the given byte
  order, which the type requires, as for every type wider than 8 bits.
- **Writing rounds each part once, from the binary64 value to nearest, ties to even.** It does not
  go through binary32: rounding twice can land on a different value. For example,
  `1 + 2^−11 + 2^−40` rounds to `1 + 2^−10` directly, but through binary32 it becomes the tie
  `1 + 2^−11` first, which then rounds to 1. Both NumPy's `float16` cast and .NET's `(Half)double`
  round once.
- **Beyond the range is ±inf**, as for `f32`. The largest finite value is 65504, and values from
  65520 up round to inf. A float type stores what the IEEE rounding gives, while an integer type
  has no inf to give, so only the integer types reject. NaN and ±inf are stored as they are.
  Subnormals (down to `2^−24`) are kept, not flushed to zero.
- **Reading** widens exactly to binary64, as for `f32`.
- **Expected values**: the files generator packs binary16 by hand with exact rational rounding
  (sign, biased exponent, 10-bit mantissa, subnormals, overflow). Wherever `struct`'s `e` format
  can pack the value, the generator checks its bytes against it. By-hand cases:
  - 1.0 is `0x3C00`;
  - the smallest subnormal `2^−24` is `0x0001`;
  - 65504 is `0x7BFF`, and 65520 is `0x7C00` (inf);
  - the double-rounding case above is `0x3C01`.

## Consequences

- `f16` keeps about three significant decimal digits: enough for quantized receiver data, not for
  analysis results.
