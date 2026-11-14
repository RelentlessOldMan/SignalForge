# ADR 0063: OFDM in the link

Status: accepted, 2026-11-13

## Context

[ADR 0060](0060-ofdm.md) gave OFDM blocks with a cyclic prefix and no synchronization. Run through
the link, a receiver has to find the frame, remove the carrier offset (which breaks the
subcarriers' orthogonality), estimate the channel on each subcarrier and keep the phase as the
offset estimate's small error accumulates. Each step has several textbook choices, and the noise
level and the expected BER have to be defined so the two languages and the theory agree.

## Decision

- `modulation = "ofdm"`: Gray QPSK on the subcarriers, with three new config fields:
  `ofdm_nfft` [64] (`N`, at least 2), `ofdm_cp_len` [16] (`1 ≤ cp ≤ N`) and `ofdm_subcarriers`
  [none: every index from `−⌊N/2⌋` to `N − 1 − ⌊N/2⌋` but 0], the used indices as
  `ofdm_modulate` takes them (`U` of them). The other modulations ignore them.
- Samples are at `fs = symbol_rate · samples_per_symbol`, as for the other modulations, so
  `frequency_offset_hz` and `delay_samples` mean the same; there is no pulse shaping
  (`rrc_taps(rolloff, sps, span_symbols)` must still accept its arguments).
- `num_symbols` and `preamble_symbols` must be whole numbers of blocks of `U` symbols: `B` blocks
  in all, the first `P ≥ 1` of them known to the receiver (the PRBS, as for the other
  modulations).
- **Noise per data subcarrier:** the AWGN has variance `N₀ = 1/(2·10^(eb_n0_db/10))` per sample,
  so with the unitary DFT each used subcarrier sees `Es/N₀ = 2·Eb/N₀` and `ber_theory` is
  `qpsk_ber_theory(eb_n0_db)`. The prefix and the empty subcarriers carry energy that this
  `Eb/N₀` does not count; a caller who wants the energy per transmitted bit adds
  `10·log10((N + cp)/N)` dB.
- **Not supported:** phase noise, clock offset and the tracking-loop gains (each must be 0 or
  none), and `|frequency_offset_hz| ≥ fs/(2N)` (half a subcarrier spacing, where the prefix
  estimate wraps).
- **Receiver:**
  1. Timing and frequency from the cyclic prefix (van de Beek, Sandell and Börjesson): for each
     frame start `d` that fits, `γ(d)` sums `r[n]·conj(r[n + N])` over the prefix samples of every
     block, and `Φ(d)` sums `(|r[n]|² + |r[n + N]|²)/2` over the same samples; `d₀` is the first
     maximum of `|γ(d)| − Φ(d)` (their metric with `ρ = 1`: at most 0, and 0 exactly at the true
     start when noiseless, where a bare `|γ|` can lose to a shifted window with few blocks), and
     `f̂ = −arg γ(d₀)·fs/(2πN)`.
     The prefix fixes the timing only within a block: with a delay longer than a block, the start
     one block early puts block 0 on the leading zeros (which add nothing to either sum) and
     every other block on its predecessor, so noiseless it ties. So the frame start is then the
     first `d` in `d₀ mod (N + cp)`, plus whole blocks, that maximizes the magnitude of the
     correlation of the derotated samples with the known samples of the `P` preamble blocks.
  2. The frame from `d₀` is derotated by `f̂` (phase 0 at `d₀`) and demodulated.
  3. Channel: `Ĥ_k`, the mean over the `P` preamble blocks of received over sent, per subcarrier.
  4. Equalize by `Ĥ_k`, then remove each block's common phase, decision-directed: the angle of
     `Σ_k w_k·conj(q(w_k·e^{−jθ_{b−1}}))`, `q` the QPSK decision, `θ_{−1} = 0`.
  5. Report: `timing_offset = d₀ mod sps`, `frame_start = ⌊d₀/sps⌋`, `frequency_offset_hz = f̂`,
     `phase_offset = arg Σ_k Ĥ_k`, EVM and bit errors over every block, preamble included.
- `ber_theory` assumes the channel is known exactly. The least-squares estimate from `P` blocks
  adds noise of variance `N₀/P` to each `Ĥ_k`; at moderate SNR this costs roughly
  `10·log10(1 + 1/P)` dB (a Gaussian approximation, used only to bound tests).

## Consequences

- An OFDM link with delay, carrier offset and noise runs in both languages and is compared like
  the others.
- A multipath channel, pilots, phase noise (common phase error and inter-carrier interference)
  and a clock offset (sampling drift across subcarriers) are left for later; the per-subcarrier
  estimate is already the place a multipath channel would be corrected.
