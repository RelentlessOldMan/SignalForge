# ADR 0103: Multiterm Lomb-Scargle periodogram

Status: accepted, 2026-11-16. Extends [ADR 0081](0081-generalized-lomb-scargle.md).

## Context

A single sinusoid fits a non-sinusoidal periodic signal poorly: a square wave, an eclipse or a
sawtooth spreads its power over harmonics. The periodogram then also peaks at fractions of the
true frequency. Fitting the harmonics together at each trial frequency puts the signal's
power back in one peak (VanderPlas & Ivezić 2015, the multiterm periodogram).

## Decision

- Python `lomb_scargle_multiterm(times, values, frequencies, terms, *, uncertainties=None,
  normalization="standard")`. C# `Spectral.LombScargleMultiterm(times, values, frequencies, terms,
  uncertainties = null, normalization = Standard)`. The arguments are those of
  `generalized_lomb_scargle`, plus `terms`, an integer `≥ 1`.
- For each `f`, the model is `c + Σₖ (aₖ cos kωt + bₖ sin kωt)` for `k = 1 … terms`, with
  `ω = 2πf`. It is fitted with weights `1/σ²`. `"standard"` returns `(χ²₀ − χ²)/χ²₀`, and
  `"power"` returns `½(χ²₀ − χ²)`, as in ADR 0081.
- The fit is solved by modified Gram-Schmidt on weighted, centered columns, with the same steps
  in both languages:
  - The weights are `wₙ = (1/σₙ²)/W`. Write `⟨a, b⟩ = Σ wₙaₙbₙ`.
  - The columns are taken in the order `cos ωt, sin ωt, cos 2ωt, …`, with the argument computed
    as `(ω·k)·t`. Each column has its weighted mean subtracted, which accounts for `c`.
  - Each column has its projections onto the kept columns removed, one at a time in order:
    `q ← q − (⟨q, qᵢ⟩/⟨qᵢ, qᵢ⟩)·qᵢ`.
  - It is dropped if `⟨q, q⟩ < 1e-12`, the ADR 0081 threshold. Otherwise its share
    `⟨y_c, q⟩²/⟨q, q⟩` is added, with `y_c` the centered values.
  - The sum `S` of the shares is the explained fraction of the weighted scatter. The standard
    value is `S/YY`, and the power is `½·W·S`.
- A dropped column is one the earlier columns already span, to within the threshold. Examples
  are a harmonic that aliases onto an earlier one, the sine at Nyquist on even samples, or more
  columns than samples allow. The fit then uses the columns that are left, which is the
  minimum-norm least-squares answer's `χ²`.
- With `terms = 1` this is the same fit as `generalized_lomb_scargle`. It is solved by
  projection rather than by the `τ` rotation, so the two agree to rounding, except where a
  column sits right at the threshold.
- There is no false-alarm formula for it: the ADR 0062 form with `d = 2·terms + 1` would be
  exact for a single frequency, but it is not wired up.

## Consequences

- Expected values come from a stdlib generator. At each frequency it solves the full
  `(2·terms + 1)`-column normal equations of the uncentered model, constant included, in exact
  rational arithmetic (`fractions.Fraction`). It starts from the floating-point cosines and
  sines of `math`. It gets `χ²` directly, with no centering and no Gram-Schmidt. Its cases avoid
  singular designs.
- By hand, on times `0 … 7` at `f = 1/8`, the square wave `1, 1, 1, 1, −1, −1, −1, −1`:
  - Its DFT has power only at the odd bins, with `|X₁|² = 4/sin²(π/8)` and
    `|X₃|² = 4/sin²(3π/8)`, out of `Σ|X|² = 64`.
  - `terms = 1` explains `2|X₁|²/64 = (1 + √2/2)/2`. `terms = 2` explains the same, because the
    even bins are 0.
  - `terms = 3` explains all of it. `terms = 4` adds the Nyquist sine, which is 0 on the
    integers and so is dropped, and still explains all of it.
- A cost of `N·terms²` per frequency, against `N` for the single-term forms.
