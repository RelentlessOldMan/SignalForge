# ADR 0635: Least-squares equalizer taps at a power-of-2 scale

Status: accepted, 2026-11-26. Amends ADR 0072.

## Context

`dfe_least_squares` builds the normal equations from products of the samples with each other,
with the training, and of the training with itself. Near 2^1000 those products overflowed and
the taps were NaN; near 2^−1000 they underflowed to 0, and the solve refused the training as not
determining the taps. The taps themselves were in range. Both languages had these faults. A
scale probe of the modules outside the measurement module found them.

## Decision

Each record is scaled by its own power of 2: the samples by `2^−e_x` and the training by
`2^−e_t`, each bringing the record's largest real or imaginary magnitude into [1, 2). The solve
then runs as before. Fitting `t ≈ w·x + b·t_past` to the scaled records gives the same feedback
taps `b` and forward taps `w·2^(e_x − e_t)`, so the forward taps are scaled back by
`2^(e_t − e_x)`.

Each record has its own scale rather than one shared scale, because the samples and the training
need not be near each other in size: samples near 2^1000 with unit training are a channel with a
huge gain, and their forward taps near 2^−1000 are in range.

## Consequences

- Results can differ from before in the last bits. The two blocks of the normal equations now
  have a different relative scale, which can change which row partial pivoting picks.
- Limitation: a forward tap whose true value is below the smallest normal double comes out
  subnormal or 0, as any double result would.
- New vectors: `dfe_least_squares.huge` and `.tiny` (case echo_inverse_by_hand with both records
  times 2^±1000), `.samples_huge` and `.samples_tiny` (only the samples scaled, so the forward
  taps scale by 2^∓1000), `.fractional_huge` and `.fractional_samples_tiny` (case
  qam16_fractional). The echo cases take the by-hand taps `w = 1`, `b = −h`, since the solved
  taps' rounding residue would turn subnormal. All use a relative tolerance only. All 6 failed
  in Python before the change. Mutation checks, in each language: no scaling failed all 6, and
  not scaling the forward taps back failed 12 cases.
