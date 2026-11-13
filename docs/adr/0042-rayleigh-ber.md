# ADR 0042: QPSK error rate in Rayleigh fading

Status: accepted, 2026-11-13

## Context

With `rician_fading` in the channel, a link test needs the curve it should follow. Over a
Rayleigh gain the AWGN error rate averages to a closed form; the general Rician case needs a
numerical integral (or a Marcum Q function).

## Decision

- `qpsk_ber_rayleigh_theory(eb_n0_db)`: Gray QPSK, coherent detection with the true gain, mean
  Eb/N0 in dB, `½·(1 − √(γ/(1+γ)))` in the form that keeps its precision at high `γ`.
- Only Rayleigh for now: the Rician curve is left until a test needs it.
- Same argument rules as `qpsk_ber_theory` (NaN rejected, `±∞` allowed).

## Consequences

- Vectors come from the closed form and are checked in the generator against a numerical average
  of `½·erfc(√(γx))` over the exponential density of `x = |g|²`.
- The Monte-Carlo check runs `rician_fading` with `K = 0`, one gain per symbol.
