# ADR 0110: Second-order intermodulation and IP2

Status: accepted, 2026-11-16. It extends [ADR 0107](0107-two-tone-imd.md) to second order.

## Context

Two tones through an even-order nonlinearity give products at the difference `f₂ − f₁` and at
the sum `f₁ + f₂`. In a direct-conversion receiver the difference product lands at baseband,
where no filter can remove it. So IP2 is quoted next to IP3.

## Decision

- Python `two_tone_ip2(samples, sample_rate, f1, f2, *, window="blackman_harris", beta=None,
  width=None)`, and C# `Measurements.TwoToneIp2(...)`.
  - Both take real or complex samples.
  - It is a new function, so `two_tone_imd`'s result does not change. The two share their
    code.
- **The groups.** These are claimed in order on the same spectrum as ADR 0107: DC, `f1`, `f2`,
  then the difference `f₂ − f₁`, then the sum `f₁ + f₂`. Both products are aliased as the
  harmonics are.
  - The rules for `f1 < f2`, for `f2`, and for a group landing on one already claimed are
    those of ADR 0107. For complex tones near `±fs/2`, the difference wraps
    and can land on DC, and is then rejected.
  - The third-order products are not claimed. A product that happens to land on one is
    measured with it.
- The result is `TwoToneIp2`, with the fields of `TwoToneImd` and `ip2_db` in place of `ip3_db`.
  - The products come difference first, then sum.
  - `imd_dbc = 10·log10(P_IM2 / P_t)`, where `P_t` is the mean of the two tone powers.
  - `worst_imd_dbc` is the larger of the two, as for IP3.
  - `ip2_db = 10·log10 P_t − worst_imd_dbc`. That is where the slope-1 and slope-2 lines meet,
    `2P_t − P_IM2` in dB. It is `+∞` when neither product has power.

## Consequences

- **Vectors.** These are worked by hand.
  - For `y = x + a₂x²` on `A₁cos ω₁n + A₂cos ω₂n`, both products have amplitude `a₂A₁A₂`, and
    the tones are untouched.
  - The square also adds DC and the second harmonics. The frequencies are chosen so that
    neither falls on a group.
  - For complex input `y = x + a₂|x|²` on `A(e^{jω₁n} + e^{jω₂n})`, the result has a line
    `a₂A²` at each of `±(ω₂ − ω₁)` and nothing at the sum. That covers the `−∞` path.
- **Tests.** A small drive extrapolates to the textbook intercept `A_IP2 = 1/|a₂|`. That is
  `ip2_db = 10·log10(1/(2a₂²))`.
