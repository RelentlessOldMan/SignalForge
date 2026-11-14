# ADR 0058: Unsigned SigMF sample types

Status: accepted, 2026-11-13

## Context

SigMF names unsigned integer sample types (`u8`, `u16`, `u32`, real or complex, with a byte order
for the wider ones) alongside the signed ones, and common receivers record unsigned 8-bit I/Q.
SignalForge rejected them ([ADR 0012](0012-signal-files.md)). The format describes the bit
layout of each type but not what sample value a code stands for, so the scaling is ours to
define, as it was for the signed types.

## Decision

- `u32`, `u16` and `u8` join the types, named like the signed ones: `cu8`, `ru8` (no order),
  `cu16_le`, `ru32_be` and so on.
- They are offset binary: code `u` of a `b`-bit unsigned type is the sample
  `(u − 2^(b−1)) / 2^(b−1)`. Mid-scale `2^(b−1)` is 0.0, code 0 is −1.0, and the top code is
  `1 − 2^(1−b)`, the same range and step as the signed type of the same width. This is how WAV
  stores 8-bit PCM, which SignalForge already reads that way ([ADR 0055](0055-wav.md)).
- Writing is the signed rule with the offset added: `round(x·2^(b−1)) + 2^(b−1)`, half to even,
  rejected outside `0 … 2^b − 1`. So a `b`-bit unsigned code is the signed code with its top bit
  flipped, and the two languages can share one code path.

## Consequences

- Recordings from receivers that store unsigned 8-bit I/Q read with no conversion step. Some
  tools center such data on 127.5 instead of 128; SignalForge reads 128 as zero, so their DC
  shows as an offset of half a code (`2^−8` of full scale). Callers who want the other centering
  subtract it.
- The cross-language file exchange covers the new types, since it runs over every datatype.
- Other types SigMF names (`f16` and wider or narrower integers) stay rejected.
