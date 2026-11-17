# ADR 0221: Schur recursion

Status: accepted, 2026-11-17. It is the alternative to ADR 0149's Levinson-Durbin.

## Context

Levinson-Durbin forms the filter `a` at every order, and each step's inner product depends on
the whole previous filter. The Schur recursion gets the same reflection coefficients from two
generator sequences that update element by element. This suits parallel and fixed-point
hardware, and it is what lattice coders use when they never need `a`.

## Decision

- **The API.**
  - Python: `schur(r, order)` in `dsp`, which returns `Schur(reflection, error)`.
  - C#: `Dsp.Schur`, which returns `Schur` for real input and `ComplexSchur` for complex input.
  - The reflection coefficients have the type of the input. `error` is real.
- **The value.**
  - Start with `u_0[i] = v_0[i] = r[i]` for `i = 0 … p`, and `E_0 = r[0]`.
  - At step `m = 1 … p`:
    - `k_m = −u[m]/E_{m−1}`;
    - `u'[i] = u[i] + k_m·v[i−1]`;
    - `v'[i] = v[i−1] + conj(k_m)·u[i]`;
    - `E_m = E_{m−1}(1 − |k_m|²)`.
  - `u` is the forward prediction error correlated with the lags, and `v` is the backward one.
    `u[m]` is exactly Levinson's inner product, so `k` and `E` equal `levinson(r, p)`'s values.
- **The rules.** They are the same as `levinson`:
  - `r` must be finite and have at least `order + 1` lags.
  - `r[0]` must be real and positive.
  - `order` must be an integer `≥ 1`.
  - Any `|k| ≥ 1` raises.

## Consequences

- **Vectors.**
  - The expected values are exact fractions, including ADR 0214's `r = [1, −1/2, 19/40]`,
    which gives `k = [1/2, −3/10]` and `E = 273/400`.
  - The generator computes `k` with an independent fraction Levinson. It checks each result by
    rebuilding the normal equations.
