# ADR 0284: Linkwitz-Riley crossover

Status: accepted, 2026-11-17.

## Context

A loudspeaker crossover splits a signal into a low band and a high band that add back to a flat
magnitude. A Linkwitz-Riley crossover of order `2N` squares a Butterworth of order `N` on each
side. Both outputs are then −6.02 dB at the cutoff and in phase there. Their sum is an all-pass:
its magnitude is 1 at every frequency. It reuses the Butterworth design and the second-order
section conventions already here.

## Decision

- **The API.**
  - Python: `linkwitz_riley(order, cutoff, sample_rate)` in `dsp`, returning a new frozen
    dataclass `Crossover(low, high)`. Each field is a section array of shape `(sections, 6)`.
  - C#: `Dsp.LinkwitzRiley(order, cutoff, sampleRate)`, returning
    `sealed record Crossover(double[][] Low, double[][] High)`.
- **The value**, with `N = order/2`:
  - `low` is the sections of `butterworth_lowpass(N, cutoff, fs)`, followed by the same
    sections again.
  - `high` is the same arrangement of `butterworth_highpass(N, cutoff, fs)`.
  - When `N` is odd, the first `high` section's `b0, b1, b2` are negated. Without that the two
    bands would be in antiphase and cancel at the cutoff.
- **The responses.**
  - `|H_low(f)| = 1/(1 + (t/K)^(2N))` and `|H_high(f)| = 1/(1 + (K/t)^(2N))`, with
    `t = tan(πf/fs)` and `K = tan(π·cutoff/fs)`. Both are exactly 1/2 at the cutoff.
  - `|H_low + H_high| = 1` everywhere.
- **The rules.**
  - `order` must be an even integer, at least 2 and at most 2000.
  - `0 < cutoff < fs/2`, finite, with the Butterworth design's rejection of cutoffs that round
    to a pole on the unit circle.

## Consequences

- **Vectors.**
  - Expected sections come from the stdlib Butterworth biquad formulas, the derivation that
    `vectors/generators/iir.py` uses, arranged as above.
  - The generator checks the all-pass sum and the 1/2 at the cutoff numerically.
  - The tolerance is `abs 1e-12, rel 1e-12`, as for the Butterworth designs.
