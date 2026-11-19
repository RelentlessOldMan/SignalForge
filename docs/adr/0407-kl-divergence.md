# ADR 0407: The Kullback–Leibler divergence

Status: accepted, 2026-11-19.

## Context

The two-sample measures so far (ADRs 0400–0406) take raw samples. Spectra, histograms and
symbol counts arrive as discrete distributions, and the Kullback–Leibler divergence is the
basic way to compare them: the expected extra information, in nats, when values drawn from
`P` are coded with a code built for `Q`.

## Decision

- **The API.**
  - Python: `kl_divergence(p, q)` in `measurements`, giving a float.
  - C#: `Measurements.KlDivergence(ReadOnlySpan<double> p, ReadOnlySpan<double> q)`.
  - `p` and `q` need not sum to 1: each is divided by its own sum, so counts and power
    spectra can be passed as they are.
- **The value.**
  - `D(P‖Q) = Σᵢ Pᵢ·ln(Pᵢ/Qᵢ)` in nats, `Pᵢ = pᵢ/Σp`, `Qᵢ = qᵢ/Σq`.
  - Each sum is taken in order; each `Pᵢ` and `Qᵢ` is one division; each term is
    `Pᵢ·ln(Pᵢ/Qᵢ)`, one division, the natural logarithm and one product; the terms are summed
    in order. Terms with `pᵢ = 0` are dropped (the limit `0·ln 0 = 0`).
  - A result below zero from rounding is returned as 0, since `D ≥ 0`.
  - Not symmetric.
- **The rules.**
  - Both one-dimensional, real, finite and non-negative, of equal length at least 1.
  - Each sums to more than zero.
  - `qᵢ = 0` where `pᵢ > 0` is an error: the divergence is infinite, and a caller who wants
    that should smooth `q` first.

## Consequences

- The cost is one pass for the sums and one for the terms.
- **Vectors.**
  - The generator forms `Pᵢ` and `Qᵢ` exactly in rationals and the logarithms in 40-digit
    decimal.
  - The tolerance is `abs 1e-15, rel 1e-13`.
