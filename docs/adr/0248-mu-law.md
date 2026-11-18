# ADR 0248: μ-law companding

Status: accepted, 2026-11-17.

## Context

Speech codecs, telephony models and low-bit-depth audio studies compress a signal's amplitude
logarithmically before quantizing it, and expand it afterwards. The continuous μ-law curve is the
textbook form. G.711 uses a segmented 8-bit approximation of it, which is out of scope here.

## Decision

- **The API.**
  - Python: `mu_law_compress(samples, mu=255.0)` and `mu_law_expand(samples, mu=255.0)` in `dsp`.
  - C#: `Dsp.MuLawCompress` and `Dsp.MuLawExpand`, with the same defaults.
  - Real samples on `[−1, 1]`.
- **The value.**
  - Compress: `y = sign(x)·ln(1 + μ|x|)/ln(1 + μ)`.
  - Expand: `x = sign(y)·((1 + μ)^|y| − 1)/μ`.
  - Both are computed with `log1p` and `expm1`. Compress is `log1p(μ|x|)/log1p(μ)`, and expand is
    `expm1(|y|·log1p(μ))/μ`. In C# these are `double.LogP1` and `double.ExpM1`.
  - The sign is applied last, and `sign(0) = 0`.
  - The two are inverses, up to rounding.
- **The rules.**
  - `mu` must be finite and `> 0`.
  - The samples must be real, finite, non-empty and within `[−1, 1]`.

## Consequences

- **Vectors.**
  - Exact anchors for `μ = 255`. `x = 1/255`, `3/255`, `15/255` and `1` compress to `1/8`, `1/4`,
    `1/2` and `1`, because `1 + μx` is `2`, `4`, `16` and `256`. Expanding them gives the inputs
    back.
  - Other values come from the formula in the generator, using the standard library's `log1p`
    and `expm1`, with a tolerance of about 1e-15.
