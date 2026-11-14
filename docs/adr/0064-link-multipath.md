# ADR 0064: Multipath in the OFDM link

Status: accepted, 2026-11-13

## Context

The OFDM link ([ADR 0063](0063-ofdm-link.md)) estimates the channel per subcarrier but only ever
met a flat one. `multipath` ([ADR 0038](0038-multipath.md)) gives a static tapped delay line. Two
things change with a delay spread: the prefix metric and the preamble correlation both find a
start anywhere from the first path to the strongest, and a DFT window that starts even a sample
late takes in the next block. The expected BER also changes, since each subcarrier now sees its
own gain.

## Decision

- Two config fields, `multipath_delays` (integers `≥ 0`) and `multipath_gains` (`[re, im]` pairs,
  finite), both none [the default] or of equal non-zero length, applied as
  `multipath(tx, delays, gains)` first in the channel, before the carrier offset, with `max(delays)`
  zeros added to `tx` first so the received signal holds every echo and the timing search reaches
  the latest start ([ADR 0065](0065-ofdm-phase-noise-clock.md) makes that tail `⌊cp/2⌋` zeros
  for every OFDM run). Only `"ofdm"`
  accepts them for now: the single-carrier chains have no equalizer, so their `ber_theory` would
  not hold ([ADR 0067](0067-link-equalizer.md) lets them take multipath with an equalizer). OFDM needs `max(delays) ≤ ⌊cp/2⌋`.
- **Back-off:** after timing gives `d₁`, the DFT windows are taken from `d₂ = max(d₁ − ⌊cp/2⌋, 0)`.
  A window is clear of the previous block's echo when `d₂ ∈ [delay + D − cp, delay]` for the
  largest path delay `D`; `d₁` lies between `delay` and `delay + D`, so `D ≤ ⌊cp/2⌋` keeps it clear.
  The window shift is a known phase ramp `e^{−j2πk(d₁ − d₂)/N}` on subcarrier `k`; it sits in
  `Ĥ_k` and the equalizer removes it. The derotation keeps phase 0 at `d₁`, and `phase_offset`
  takes the ramp back out, so without multipath it means what it did before.
- **Expected BER:** `H_k = Σᵢ gᵢ·e^{−j2πk·dᵢ/N}` for subcarrier `k`, and `ber_theory` is the mean
  over the used subcarriers of `qpsk_ber_theory(eb_n0_db + 10·log10|H_k|²)`, with `1/2` where
  `H_k = 0`. Eb/N₀ stays defined before the channel. As in ADR 0063 it assumes the channel is known.

## Consequences

- The first samples of each prefix carry the previous block's echo, so the prefix's frequency
  estimate is a little biased under multipath (about 2·10⁻⁴ of a subcarrier spacing without noise
  for the test channel); the per-block phase absorbs most of it, and a noiseless multipath link is
  not an exact recovery.
- The per-subcarrier estimate is exercised on a frequency-selective channel, and the theory
  checks it.
- Equalizers for the single-carrier chains, fading over time and fractional path delays are later
  work.
