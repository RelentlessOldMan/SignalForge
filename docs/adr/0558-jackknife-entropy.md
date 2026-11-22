# ADR 0558: The jackknife Shannon entropy

Status: accepted, 2026-11-21.

## Context

Zahl (1977) reduces the bias of the plug-in Shannon entropy by the jackknife over
individuals: with `H₋ᵢ` the plug-in entropy after one individual of kind `i` is removed,
`H_J = N·H − (N − 1)/N · Σᵢ xᵢ H₋ᵢ`.

## Decision

- **The API.**
  - Python: `jackknife_entropy(samples)` in `measurements`, giving a float in nats.
  - C#: `Measurements.JackknifeEntropy(ReadOnlySpan<double> samples)`.
- **The value, in closed form.**
  - `S = Σ xᵢ ln xᵢ` over the values above 0 in record order, and `H = ln N − S/N`.
  - Removing one individual of kind `i` leaves `N − 1` and
    `H₋ᵢ = ln(N − 1) − (S − xᵢ ln xᵢ + (xᵢ − 1) ln(xᵢ − 1))/(N − 1)`, the last product 0 when
    `xᵢ = 1`.
  - `A = Σ xᵢ H₋ᵢ` over the values above 0 in record order; `H_J = N·H − (N − 1)/N · A`.
  - 0 in exact arithmetic when one value holds the total; the cancellation leaves a few
    units of `N · 2⁻⁵²` in floating point.
- **The rules.**
  - Whole numbers, as for the Brillouin index: real, finite, one-dimensional, at least 1
    value, every value at least 0 and whole, not all 0, totalling at most 10 000 000.
  - `N > 1`, so that `H₋ᵢ` exists (otherwise `invalid_argument`).

## Consequences

- One pass for the checks, one for `S`, one for `A`.
- `N·H` and the sum cancel to a value near `H`, so the rounding error grows with `N`.
- **Vectors.**
  - The generator forms each `H₋ᵢ` from its reduced record directly, not from the closed
    form, in 50-digit decimal.
  - The tolerance is `abs 1e-10, rel 1e-11`, for the cancellation at `N = 10 000`.
