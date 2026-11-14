# ADR 0074: A blind (constant-modulus) equalizer

Status: accepted, 2026-11-13

## Context

Every equalizer so far (ADRs 0066, 0069, 0072) needs known symbols to start: training for the LMS
and decision-feedback updates, and for the least-squares taps. A receiver that joins a stream
part-way, or a frame with no preamble, has none. The usual training-free start is the
constant-modulus algorithm (Godard, p = 2): it adapts the taps so the output's magnitude is
constant, which needs nothing but the modulus, and opens the eye far enough for decisions to take
over. It cannot see phase, so its output is turned by an unknown angle.

## Decision

- A standalone block in `sync`: `cma_equalizer(samples, num_taps, step, *, samples_per_symbol=1,
  center=None, modulus=1.0, initial_taps=None)` (C# `Sync.CmaEqualizer`), returning the
  `Equalization(symbols, errors, taps)` of the LMS equalizer.
- The same regressor, output, tap indexing, start (unit impulse at `center`, or `initial_taps`)
  and fractional spacing as the LMS equalizer, so its taps can start one.
- The error is `e = y·(R − |y|²)`, with `R = modulus` (finite, above 0), and the update
  `w ← w + (μ/P)·e·conj(u)`, normalized by the regressor power `P` as the LMS equalizer is, so
  `step` means the same at any level. `step` is in `[0, 2]` as there; it is not a stability bound
  here, and steps near 0.03 are what work.
- `R` is the caller's: `E|a|⁴ / E|a|²` for the constellation, which is 1 for the unit-power PSKs
  and 1.32 for unit-power 16-QAM. No default per modulation, because the block takes no
  modulation.
- Every output adapts; there is no training and no decision.

## Consequences

- Measured on `1 + (0.35 − 0.2j)·z⁻¹ + (−0.1 + 0.05j)·z⁻²` turned by 0.7 rad, 7 taps, step 0.03,
  3000 symbols: QPSK's mean square error after the best rotation goes to 0.006 over the last 1000,
  16-QAM's to 0.013. On the link's harder channels (a zero at radius 0.9) it settles at about 0.07
  for QPSK, short of trained LMS.
- The output carries the channel's phase and, for a long equalizer, possibly a shifted delay. A
  carrier loop or a known symbol resolves the phase; the block does not.
- The link does not use it: every link frame has a preamble, which trains the equalizer better.
  It is for receivers built from the blocks.
- Vectors come from a stdlib generator running the recurrence, plus closed-form cases (one tap on
  a scalar gain).
