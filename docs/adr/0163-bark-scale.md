# ADR 0163: Bark scale

Status: accepted, 2026-11-16. It sits beside the mel scale (ADR 0154) and the ERB scale
(ADR 0160).

## Context

The Bark scale numbers the critical bands of hearing, from about 0 to 24. There are several
formulas for it:

- Zwicker & Terhardt (1980), an arctangent sum with no closed-form inverse;
- Traunmüller (1990), `z = 26.81·f/(1960 + f) − 0.53`, with corrections at both ends that
  most libraries leave out or make optional;
- Schroeder's `asinh` form.

## Decision

- **The formula.** Traunmüller (1990), with both corrections always applied, as the paper
  gives them.
  - `z = 26.81·f/(1960 + f) − 0.53`.
  - If `z < 2`, the result is `z + 0.15·(2 − z)`.
  - If `z > 20.1`, the result is `z + 0.22·(z − 20.1)`.
  - Otherwise the result is `z`.
  - Both corrections leave the value unchanged at their edge, so the scale is continuous and
    increasing.
- **The inverse.** It is closed form.
  - First, undo the correction of the branch the value lies in: below 2, `z = (b − 0.3)/0.85`;
    above 20.1, `z = (b + 4.422)/1.22`; otherwise `z = b`. Each correction maps its branch
    onto itself, so the branch can be chosen from `b`.
  - Then `f = 1960·(z + 0.53)/(26.28 − z)`.
  - The result is clamped at 0, so rounding cannot make it negative.
- **The API.** In `units`:
  - Python: `hz_to_bark(hz)` and `bark_to_hz(bark)`, which take scalars or arrays, as the mel
    functions do.
  - C#: `Units.HzToBark` and `Units.BarkToHz`.
- **The rules.**
  - `hz` must be finite and `≥ 0`.
  - `bark` must be finite and at least `hz_to_bark(0) = −0.1505`. That bound is computed in
    floating point as `−0.53 + 0.15·(2 − (−0.53))`, so `bark_to_hz(hz_to_bark(0))` is
    accepted.
  - After the un-correction, `z` must be below `26.28`. That corresponds to `b < 27.6396`,
    the limit as `f → ∞`.
  - Anything else is `invalid_argument`.

## Consequences

- **There is no option to turn the corrections off.** A caller who wants the plain formula can
  compute it in one line. A switch can be added later without breaking anything.
- **Vectors are exact.** Every step is rational, so the generator computes in `fractions` from
  the float arguments. The cases are:
  - `f = 1960`, which gives `z = 12.875` exactly;
  - points on both sides of each branch edge: `f ≈ 204.23` for `z = 2` and `f ≈ 6542.8` for
    `z = 20.1`;
  - the inverse on both sides of 2 and 20.1;
  - the errors.
