# ADR 0117: Fifth-order intermodulation and IP5

Status: accepted, 2026-11-16. It extends [ADR 0107](0107-two-tone-imd.md) and
[ADR 0110](0110-two-tone-ip2.md) to fifth order.

## Context

Two tones through an odd-order nonlinearity give products at `3f₁ − 2f₂` and `3f₂ − 2f₁`, next to
the third-order ones and just as close in. A power amplifier's spectral regrowth past the
third-order products is set by them, and a linearizer is judged on how far it pushes them down.
IP5 is quoted for that.

## Decision

- Python `two_tone_ip5(samples, sample_rate, f1, f2, *, window="blackman_harris", beta=None,
  width=None)`, and C# `Measurements.TwoToneIp5(...)`, for real or complex samples.
  - It is a new function, built as ADR 0110 built `two_tone_ip2` and sharing its code.
- **The groups** are claimed in order on the same spectrum: DC, `f1`, `f2`, then the lower
  product `3f₁ − 2f₂`, then the upper product `3f₂ − 2f₁`.
  - Both products are aliased as the harmonics are.
  - The rules for `f1 < f2`, for `f2`, and for a group landing on one already claimed are those
    of ADR 0107.
  - The third-order products are not claimed. For distinct tones they never coincide with a
    fifth-order product (the two differ by a multiple of `f₂ − f₁`), but they can fold onto one;
    a product that lands on one is measured with it.
- The result is `TwoToneIp5`, with the fields of `TwoToneImd` and `ip5_db` in place of `ip3_db`.
  - The products come lower first, as for IP3.
  - `imd_dbc = 10·log10(P_IM5 / P_t)`, where `P_t` is the mean of the two tone powers.
  - `worst_imd_dbc` is the larger of the two.
  - `ip5_db = 10·log10 P_t − worst_imd_dbc/4`. That is where the slope-1 and slope-5 lines meet,
    `(5P_t − P_IM5)/4` in dB. It is `+∞` when neither product has power.

## Consequences

- **Vectors.** These are worked by hand.
  - The generator expands `y = x + a₅x⁵` on two coherent cosines, and `y = x + a₅|x|⁴x` on two
    complex exponentials, exactly. It works in rational arithmetic, on the exponentials' integer
    bin indices, and folds each line into the spectrum.
  - Each claimed group's power is the sum over the lines at its centre. The generator asserts
    that every other line is at least eight bins from every claimed group, so no skirt reaches
    a group.
  - For the real case `y = x + a₅x⁵` on `A₁cos ω₁n + A₂cos ω₂n`, each
    fifth-order product has amplitude `(5/8)a₅A₁³A₂²` (lower) or `(5/8)a₅A₁²A₂³` (upper).
    The quintic also adds to the tones themselves, by its own terms at `ω₁` and `ω₂`.
  - For the complex envelope `y = x + a₅|x|⁴x` on `A(e^{jω₁n} + e^{jω₂n})`, the output is
    `A e^{jω₁n}·(1 + a₅A⁴(10 + 5u + 10u* + u² + 5u*² + u*³))` with `u = e^{j(ω₁ − ω₂)n}`, so the
    fifth-order products have amplitude `a₅A⁵`.
  - A linear input gives both products no power, which covers the `+∞` intercept.
- **Tests.** For `y = x + a₅x⁵` on equal tones of amplitude `A`, the products are `(5/8)a₅A⁵` and
  the tones `A(1 + 6.25a₅A⁴)`. The tests check the intercept against that expansion at two drives,
  and that a small drive tends to the textbook `A_IP5⁴ = 8/(5|a₅|)`, `ip5_db = 10·log10(A_IP5²/2)`.
  - Products below about −150 dBc lose accuracy to rounding in the spectrum, so the tests drive
    hard enough to keep them above that.
