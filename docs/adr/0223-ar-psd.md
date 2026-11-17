# ADR 0223: AR model PSD

Status: accepted, 2026-11-17. It shares its scaling and folding with ADR 0203 and ADR 0204.

## Context

`yule_walker_psd` and `burg_psd` fit a model to samples and return its PSD. A model can also come
from somewhere else: `cepstrum_to_lpc`, `lsf_to_lpc`, `reflection_to_lpc`, a quantizer, or a
specification. The density of a given model should not need samples.

## Decision

- **The API.**
  - Python: `ar_psd(coefficients, error, sample_rate, nfft, *, one_sided=None)` in `spectral`.
  - C#: `Spectral.ArPsd(coefficients, error, sampleRate, nfft, oneSided = true)` for real
    coefficients. The complex overload has no `oneSided` and is always two-sided, as in
    ADR 0203.
  - `nfft` is required, because a model has no natural length.
- **The value.**
  - The two-sided density is `σ²/(fs·|A_k|²)`, with `A_k = Σ_j a_j e^(−2πi jk/M)` and
    `M = nfft`.
  - It is folded as Welch: a one-sided density doubles the interior bins, and a two-sided one
    is shifted.
  - With the same `a`, `σ²` and `nfft`, the bins equal those of `yule_walker_psd` and `burg_psd`.
- **The return type.** It is `SpectralDensity`, so band power, occupied bandwidth and the other
  density tools work on it unchanged.
  - The fields a model has no value for are set to the values of one segment of length `M`:
    `nperseg = M`, `num_segments = 1` and `enbw_hz = fs/M`.
  - `bin_width = fs/M`.
- **The rules.**
  - The filter must be finite, with `a[0] = 1`.
  - `error` must be positive and finite, and so must `sample_rate`.
  - `nfft` must be an integer `≥ order + 1`.
  - `one_sided = True` needs real coefficients.
  - Minimum phase is not needed, but `A_k` must not be zero on any bin.

## Consequences

- **Vectors.**
  - The expected values sum `|A_k|²` directly, as `Σ_j Σ_l a_j conj(a_l) e^(−2πi(j−l)k/M)`,
    with no FFT.
  - An order-1 case is checked against the closed form `1 + a² + 2a cos(2πk/M)`.
  - The cases cover odd and even `nfft` and both foldings.
  - The generator also checks that the density matches `yule_walker_psd`'s ADR 0203 case
    `x = [1, 2]`. That model has `a = [1, −2/5]` and `σ² = 21/10`.
