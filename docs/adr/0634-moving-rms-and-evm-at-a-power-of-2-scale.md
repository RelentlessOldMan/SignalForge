# ADR 0634: Moving RMS and EVM at a power-of-2 scale

Status: accepted, 2026-11-26. Amends ADRs 0007 and 0239.

## Context

The moving RMS squares each sample. Near 2^1000 the squares overflowed and the result was
infinite, although the RMS itself was in range; near 2^−1000 they underflowed and the result was
0. EVM sums the squared errors and the reference power, so near 2^1000 it was NaN, and near
2^−1000 it refused the reference as having no power. EVM is a ratio and does not change when
both records are scaled together. Both languages had these faults. A scale probe of the modules
outside the measurement module found them.

## Decision

- The moving RMS scales each window by the power of 2 that brings its largest magnitude into
  [1, 2). It sums the squares of the scaled magnitudes in the same order as before, and scales
  the root back up. Each window has its own scale, so a record whose loud and quiet parts
  differ by more than any one scale can hold still gives every window in range.
- EVM scales the measured and reference records by one power of 2, the one that brings the
  largest real or imaginary magnitude in either record into [1, 2), and then computes as
  before.

The scaling is exact, and the square root of `4^−e·q` is `2^−e·√q` exactly. Results that did
not overflow or underflow before are unchanged, bit for bit.

## Consequences

- Limitation: EVM uses one scale for both records, so a reference more than about 2^500 smaller
  than the measured symbols still underflows. Such a record has an EVM near 2^500 anyway.
- New vectors: `moving_rms.huge` and `.tiny` (case mixed times 2^±1000), `moving_rms.wide`
  (windows 2^2000 apart in size, which no one scale can hold), and `evm.huge` and `.tiny`
  (single_error times 2^±1000). These use a relative tolerance only: with the usual absolute
  tolerance, the original `moving_rms.tiny` passed even before the change. All 5 failed in both
  languages before the change. Mutation checks, in each language: capping the exponent at 0
  from above failed every `huge` case and `wide`, and capping it from below failed every `tiny`
  case and `wide`.
- That trap led to a check of every vector whose expected values all lie below its own
  absolute tolerance. Six were found; they are a lead in `docs/status.md`.
