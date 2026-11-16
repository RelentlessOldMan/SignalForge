# ADR 0165: A and C weighting filters

Status: accepted, 2026-11-16. It realizes the curves of ADR 0164 as IIR sections.

## Context

To weight a signal rather than a spectrum, a sound level meter filters it. The usual digital
A and C filters take the analog transfer functions behind ADR 0164 through the bilinear
transform:

- `H_A(s) ∝ s⁴/((s + ω1)²(s + ω2)(s + ω3)(s + ω4)²)`;
- `H_C(s) ∝ s²/((s + ω1)²(s + ω4)²)`;

where `ω_k = 2π f_k`, with the pole frequencies of ADR 0164. Designs differ on three points:

- prewarping;
- how the poles are paired into sections;
- where the gain is set.

## Decision

- **The API.** In `dsp`, beside the other IIR designs, returning sections `[b0, b1, b2, a0,
  a1, a2]` with `a0 = 1`:
  - Python: `a_weighting_sos(sample_rate)` and `c_weighting_sos(sample_rate)`.
  - C#: `Dsp.AWeightingSos(sampleRate)` and `Dsp.CWeightingSos(sampleRate)`.
- **The transform.** The plain bilinear transform, `s = K(1 − z⁻¹)/(1 + z⁻¹)` with
  `K = 2·fs`, and no prewarping, as in the usual designs. The digital response at `f` is
  therefore exactly the analog response at `(fs/π)·tan(π f/fs)`, so the curve bends near
  Nyquist. Callers who need it accurate up to 20 kHz should use a high sample rate.
- **The factors.** Each section is the product of two first-order factors, and each factor
  goes through the transform on its own:
  - high-pass `s/(s + ω)` becomes `b = [K, −K]/(K + ω)`, `a = [1, (ω − K)/(K + ω)]`;
  - low-pass `ω/(s + ω)` becomes `b = [ω, ω]/(K + ω)`, with the same `a`.
- **The sections, in order.**
  - A: high-pass `ω1` times high-pass `ω1`; then high-pass `ω2` times high-pass `ω3`; then
    low-pass `ω4` times low-pass `ω4`.
  - C: high-pass `ω1` times high-pass `ω1`; then low-pass `ω4` times low-pass `ω4`.
- **The gain.** The first section's `b` is divided by the cascade's magnitude at 1 kHz, so the
  filter is exactly 0 dB there.
  - That magnitude comes from the analog factors at `Ω = K·tan(π·1000/fs)`: `Ω/√(Ω² + ω²)`
    for a high-pass factor and `ω/√(Ω² + ω²)` for a low-pass one.
  - This is exact, because the bilinear transform maps `e^(jω)` to `jK·tan(ω/2)`.
- **The rules.** `sample_rate` must be finite and above 2000 Hz, so that 1 kHz is below
  Nyquist. Anything else is `invalid_argument`.

## Consequences

- **The identity is a test.** At every `f` below Nyquist, the response in dB equals
  `weighting((fs/π)·tan(π f/fs)) − weighting((fs/π)·tan(π·1000/fs))`. The tests check this
  against `a_weighting` and `c_weighting` to rounding, which ties the filter to the curve.
- **Vectors come from the closed form.** The coefficients are computed in 60-digit `decimal`,
  with π from Machin's formula and the tangent from Taylor sine and cosine. They cover several
  sample rates for each curve, and the errors.
