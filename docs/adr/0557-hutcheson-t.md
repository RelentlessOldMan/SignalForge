# ADR 0557: Hutcheson's t

Status: accepted, 2026-11-21.

## Context

Hutcheson (1970) compares the Shannon diversity of two samples with
`t = (H_a − H_b)/√(V_a + V_b)`, `H` the plug-in Shannon entropy and `V` Hutcheson's variance
(ADR 0556) of each. Its degrees of freedom are a separate quantity, not part of this one.

## Decision

- **The API.**
  - Python: `hutcheson_t(a, b)` in `measurements`, giving a float.
  - C#: `Measurements.HutchesonT(ReadOnlySpan<double> a, ReadOnlySpan<double> b)`.
- **The value.**
  - For each record, in record order over the values above 0: `L = Σ pᵢ lᵢ`, `lᵢ = ln pᵢ`,
    `H = −L`, and `V` exactly as Hutcheson's variance forms it.
  - `t = (H_a − H_b)/√(V_a + V_b)`; it changes sign when the records swap.
- **The rules.**
  - Each record as for Hutcheson's variance (whole numbers, as for the Brillouin index);
    the messages name `a` or `b`.
  - `V_a + V_b` must be above 0 (otherwise `invalid_argument`): both are 0 only when each
    record has one kind.

## Consequences

- The checks and sums of one record are a private helper both languages share between
  the two calls.
- **Vectors.**
  - The generator forms `H`, `V` and `t` in 50-digit decimal.
  - The tolerance is `abs 1e-12, rel 1e-11`, for the cancellation in `H_a − H_b` and in
    each variance.
