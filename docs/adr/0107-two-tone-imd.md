# ADR 0107: Two-tone intermodulation and IP3

Status: accepted, 2026-11-16. Builds on the tone metrics' bin groups,
[ADR 0015](0015-tone-metrics.md).

## Context

The standard linearity test is to drive a device with two equal tones close together. The
third-order products at `2f₁ − f₂` and `2f₂ − f₁` are measured, and the third-order intercept is
extrapolated from them. The products fall next to the tones, where a filter cannot remove them,
so this is the figure a receiver's dynamic range is quoted in.

## Decision

- Python `two_tone_imd(samples, sample_rate, f1, f2, *, window="blackman_harris", beta=None,
  width=None)`, and C# `Measurements.TwoToneImd(samples, sampleRate, f1, f2, window, beta,
  width)`. Both take real or complex samples. The caller names both tone frequencies, and
  `f1 < f2` is required.
- One spectrum and its groups are formed exactly as for the tone metrics, with `f1` as the
  fundamental: DC first, then `f1`. Then `f2` is grouped, then the lower product `2f₁ − f₂`,
  then the upper product `2f₂ − f₁`.
  - The products are taken from the nominal frequencies the caller gave. They are aliased into
    the spectrum's range as the harmonics are: folded for real input, wrapped for complex.
  - A group whose centre bin is already claimed is `invalid_argument`. That happens when `f2`
    is inside the `f1` group or DC, or when a product falls on DC, a tone or the other product.
    An answer there would measure the wrong thing.
  - `f2` follows the fundamental's rules (`|f| ≤ fs/2`, and `f ≥ 0` for real input), and its
    group needs power.
- The result is `TwoToneImd`, with these fields:
  - `tone_frequencies`, the two power centroids
  - `tone_powers`
  - `imd_frequencies`, the two aliased nominal frequencies, lower first
  - `imd_powers`
  - `imd_dbc = 10·log10(P_IM / P_t)`, where `P_t` is the mean of the two tone powers
  - `worst_imd_dbc`, the larger of the two
  - `ip3_db = 10·log10 P_t − worst_imd_dbc/2`. That is `P_t + (P_t − P_IM)/2` in dB, which is
    where the slope-1 and slope-3 lines meet.

  A product with no power gives `imd_dbc = −∞`, and an `ip3_db` of `+∞` when both have none.
- The worse product sets IP3, the conservative choice used on datasheets. Powers are in sample
  units² as in every other measurement, so `ip3_db` is dB of sample units², and it is
  output-referred when the samples are the output. Converting to dBm, or to the input, is the
  caller's job.
- Only third order is measured. The 5th and higher products, and IP2, can be added later.

## Consequences

- Expected values come from a cubic nonlinearity worked by hand.
  - For `y = x + a₃x³` on `A₁cos ω₁n + A₂cos ω₂n`, the product at `2ω₁ − ω₂` has amplitude
    `(3/4)a₃A₁²A₂`, and the tone at `ω₁` has `A₁ + a₃((3/4)A₁³ + (3/2)A₁A₂²)`.
  - For complex input, `y = x + a₃|x|²x` on `A(e^{jω₁n} + e^{jω₂n})` gives tones `A(1 + 3a₃A²)`
    and products `a₃A³`.
  - The frequencies are coherent with a Blackman-Harris window, whose leakage stops at three
    bins. So the group sums are exact to rounding.
- The tests also check that a small drive extrapolates to the textbook intercept,
  `A_IP3² = 4/(3|a₃|)`.
