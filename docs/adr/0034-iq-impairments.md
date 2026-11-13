# ADR 0034: IQ imbalance and DC offset

Status: accepted, 2026-11-13

## Context

A direct-conversion receiver's I and Q branches never match: their gains differ and their local
oscillators are not exactly 90° apart. That makes an image of every tone at the mirror frequency.
Two implementations could put the error on either branch, split it between them, or give the
phase the other sign; each choice moves the image's phase and the meaning of the arguments.

## Decision

- The I branch is the reference; the Q branch carries both errors:
  `y = I + j·g·(Q·cos φ + I·sin φ)`, `g = 10^(gain_db/20)`. For `x = e^{jθ}`, `Im y = g·sin(θ + φ)`,
  so `φ > 0` advances the Q branch.
- The widely linear form `y = μ·x + ν·x̄`, `μ = (1 + g·e^{jφ})/2`, `ν = (1 − g·e^{−jφ})/2`, and the
  image rejection `|μ|²/|ν|²` are in the conventions, and `iq_image_rejection_db` returns the
  latter, so a measured image can be checked against the arguments.
- `dc_offset(samples, offset)` adds one complex constant.
- Both live in the channel module with `awgn` and `frequency_offset`.

## Consequences

- A split model (half the error on each branch) differs from this one by a complex gain on the
  whole signal only; the image rejection is the same.
- Expected values: by hand (a quarter-turn error makes Q copy I; a gain of 2), and the
  widely linear form, which is independent of the branch form the libraries compute.
