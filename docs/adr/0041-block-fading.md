# ADR 0041: Block fading

Status: accepted, 2026-11-13

## Context

A mobile channel's gain wanders; over a short burst it is close to constant. The usual test
models are Rayleigh (no line of sight) and Rician (a fixed path plus scatter, its strength the
K factor). They can be built with a continuously varying gain (Jakes, filtered noise) or with
one gain held for a block of samples.

## Decision

- `rician_fading(samples, k_factor, block_length, *, seed)`: one gain per block of
  `block_length` samples, `√(K/(K+1)) + √(1/(K+1))·CN(0, 1)`, unit mean power. Rayleigh is
  `k_factor = 0`; there is no separate function.
- Block fading is what a BER-against-theory test needs (the average of the AWGN curve over the
  gain distribution), and `block_length = 1` gives fast fading with independent gains.
- The line-of-sight phase is 0. A caller who wants another phase multiplies by it.
- `k_factor = ∞` is accepted and means no fading, so a sweep of K can end at the AWGN case.

## Consequences

- Continuous (Doppler-shaped) fading is a later model with its own definition.
- Random streams differ between languages, so the vectors are the deterministic cases (K = ∞,
  empty input, bad arguments); the unit tests check the gain's statistics against theory.
