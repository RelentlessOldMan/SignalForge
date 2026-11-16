# ADR 0111: ACPR through a root-raised-cosine channel filter

Status: accepted, 2026-11-16. It extends ACPR, [ADR 0019](0019-acpr.md).

## Context

ADR 0019 integrates each channel as a rectangle. The 3GPP (WCDMA) and TETRA ACLR measurements
instead weight each channel by a root-raised-cosine receive filter. The power is then the PSD
times `|H(f)|²`, a raised cosine. Rectangles over a shaped spectrum read differently, so the
filtered figure needs its own call.

## Decision

- Python `acpr_rrc(frequencies, psd, center, symbol_rate, alpha, offsets, *, span=None)`, and C#
  `Spectral.AcprRrc(...)`. It returns the same `Acpr` result as `acpr`.
  - It is a new function rather than a `weighting` argument, because the bandwidth argument
    changes meaning: here it is the symbol rate `R`.
  - Every channel, main and adjacent, uses the same filter.
- **The weight.** The weight is `G(f) = |H(f)|²` of an RRC with roll-off `α`, with a peak of 1:
  - `1` for `|f| ≤ (1 − α)R/2`
  - `½(1 + cos(π(|f| − (1 − α)R/2)/(αR)))` up to `(1 + α)R/2`
  - `0` beyond that
- **The power.** A channel centred at `c` has power `Σ psd_k·Δ·G(f_k − c)` over the bins: each
  bin's power (as in ADR 0019's bins), weighted at its centre.
  - No partial bins are taken. The weight is smooth, and the raised cosine has a useful
    property here.
  - Its Fourier transform, the raised-cosine pulse, is zero at every nonzero multiple of `1/R`.
    So by Poisson summation, the bin sum of a flat PSD is exactly `psd·R` whenever `R/Δ` is a
    whole number, wherever the bins fall.
- **The channels.** The main channel is centred at `center`. For each offset `o`, the adjacent
  channels are centred at `center ∓ o`.
- **Arguments.**
  - Each channel's support `c ± (1 + α)R/2` must lie inside the spectrum, with ADR 0019's
    edges, span and `1e-9` slack.
  - `center` is finite. `symbol_rate` is finite and `> 0`. `0 < α ≤ 1`. `α = 0` is excluded,
    because a rectangle weighted at bin centres is not the rule above. `acpr` covers it.
  - `offsets` and `main_power > 0` are as for `acpr`.
- The dBc values are computed as in ADR 0019, as a difference of logs.

## Consequences

- **Vectors.** These are worked by hand.
  - A flat PSD gives `level·R` in every channel, exactly. A step from one level to another,
    away from each channel's support, gives the ratio of the levels.
  - A single line in one bin reads its power times `G` at its offset, from the formula above.
    That checks the taper.
- **Tests.** An RRC-shaped QPSK signal's own channel holds almost all of its power. A white
  noise PSD reads the same `R·N₀` in every channel.
