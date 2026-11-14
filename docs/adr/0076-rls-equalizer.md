# ADR 0076: A recursive-least-squares equalizer

Status: accepted, 2026-11-13

## Context

The normalized LMS equalizer (ADR 0066) and its decision-feedback form converge slowly when the
channel's spectrum is far from flat, as with a zero near the unit circle: the input's correlation
matrix is badly conditioned, and LMS converges at the pace of its smallest eigenvalue. The
least-squares start (ADR 0072) solves the preamble once but does not adapt. Exponentially
weighted recursive least squares (RLS) adapts with a convergence time of about twice the tap
count whatever the conditioning, at `O(L²)` work per symbol instead of `O(L)`.

## Decision

- A block in `sync`: `rls_equalizer(samples, training, num_taps, forgetting, *, delta=0.01,
  samples_per_symbol=1, center=None, decision=None, initial_taps=None)` (C#
  `Sync.RlsEqualizer`), returning the LMS equalizer's `Equalization(symbols, errors, taps)`.
- The LMS equalizer's regressor, output `y = Σ w_i·u_i`, start (unit impulse at `center`, or
  `initial_taps`), fractional spacing, training and decisions; only the update differs.
- The standard exponentially weighted RLS update for an output written `y = wᵀu`: the inverse
  correlation `P` starts at `I/δ`; with a reference, `g = P·conj(u) / (λ + uᵀ·P·conj(u))`,
  `w ← w + g·e`, `P ← (P − g·(uᵀ·P))/λ`. The order of every sum is fixed in the conventions, so
  the languages agree to rounding.
- `forgetting` `λ` in `(0, 1]` (1 is growing-window least squares); `delta` `δ` finite and above
  0. No update, and `P` unchanged, when there is no reference or the regressor is all zero (as
  the LMS equalizer skips a zero-power regressor); this also keeps `P` from growing as `λ⁻ⁿ`
  through silence.
- Forward taps only. Feedback taps and the phase loop stay with `dfe_equalizer`; the link does
  not use RLS yet.

## Consequences

- Measured on `1 + 0.9·e^{0.6j}·z⁻¹` (a zero at radius 0.9), QPSK, noise σ = 0.05 per component,
  15 taps with the center at 2, trained throughout, mean over 20 seeds: RLS (λ = 1, δ = 0.01) has
  a mean square error of 0.06 over symbols 25–49 and about 0.03 from then on; normalized LMS has
  0.32 (step 0.5) and 0.51 (step 0.1) there, and is still at 0.11 and 0.16 after 400 symbols.
- With `λ = 1` and every output trained, the taps after `n` updates are the regularized
  least-squares solution `(δI + Σ conj(u_k)u_kᵀ)⁻¹(δ·w₀ + Σ conj(u_k)·d_k)`; with `λ < 1` the same
  with weights `λ^{n−k}` and `λⁿδ`. The vector generator checks its recurrence against this
  closed form, which is an independent derivation of the same quantity.
- `P` is held as a full matrix, not forced Hermitian; at `λ` near 1 and these lengths rounding
  stays far below the tolerances. Long runs at small `λ` with little excitation can still lose
  precision, as RLS is known to.
- `O(L²)` per symbol: fine for the tens of taps the link uses.
