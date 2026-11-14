# ADR 0068: Frame search in blocks

Status: accepted, 2026-11-13

## Context

The single-carrier chains find the frame start (conventions: QPSK link, Receiver, step 3) by
correlating the whole preamble coherently with the coarsely derotated symbols. The coarse
frequency estimate is not exact: for QPSK it is off by about 0.7 Hz rms on a flat 1 kHz link at
6 dB, and by about twice that through strong inter-symbol interference. Over a preamble of `P`
symbols the residual turns the correlation by `2π·Δf·P/R`, a full cycle at `P = 1000` and
`Δf = 1 Hz`, and the correlation's magnitude falls to its sidelobes' level, so the search can pick
the wrong start. The equalizer (ADR 0067) wants preambles that long; this happened in testing.

## Decision

- Step 3 correlates in **blocks of `B = phase_block_symbols`** symbols and adds the blocks'
  magnitudes: `q(k) = Σ_b |Σ_{i ∈ block b} conj(a[i])·c[k+i]|`, the blocks `[bB, min((b+1)B, P))`.
  The frame start is still the first `k` that maximizes it.
- `B` is reused rather than a new field: it is already the span over which the chain treats the
  phase as constant (step 4), and the default `P = B = 32` keeps one block, so the search is
  exactly the old one and default runs do not change.
- Within a block the residual turns the phase by `2π·Δf·B/R`, 0.3 rad at 1.4 Hz and `B = 32`,
  which costs about 1% of the block's magnitude.

## Consequences

- Adding magnitudes is noncoherent: below about 0 dB per block the noise adds a bias to every
  `k` alike, and the peak still stands out by roughly `√(number of blocks)` over the sidelobes.
- Runs with `P > B` may find a different (correct) start than before; their noisy results change.
- The fine frequency and phase (steps 4–6) are unchanged.
