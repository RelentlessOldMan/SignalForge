# ADR 0293: Channel vocoder

Status: accepted, 2026-11-17.

## Context

A channel vocoder makes one signal, the carrier (often a synth), speak with the spectral
envelope of another, the modulator (often a voice). Both pass through matching banks of
band-pass filters. The envelope of each modulator band sets the level of the matching carrier
band, and the carrier bands are summed. The parts exist: the state-variable band-pass
(ADR 0279) and the envelope follower (ADR 0238).

## Decision

- **The API.**
  - Python: `vocoder(carrier, modulator, bands, low, high, q, attack, release, sample_rate)` in
    `dsp`.
  - C#: `Dsp.Vocoder(...)` with the same arguments in PascalCase.
  - Real signals only.
- **The bands.**
  - Band `k` of `bands` is centred at `f_k = low·(high/low)^((k + 1/2)/bands)`. That splits
    [low, high] into `bands` equal widths on a log scale and puts each centre in the middle of
    its width.
  - Each band is `(1/q)·svf(·, f_k, q, fs, output="bandpass")`, unity gain at its centre.
- **The value.**
  - `y = Σ_k C_k·envelope_follower(M_k, attack, release)`.
  - `C_k` and `M_k` are the carrier's and the modulator's band `k`.
- **The rules.**
  - The carrier and the modulator are real, finite, non-empty and the same length.
  - `bands` is an integer from 1 to 1000.
  - `0 < low < high < fs/2`.
  - The SVF's rule for `q`, and the envelope follower's rules for `attack` and `release`.

## Consequences

- **Vectors.**
  - Expected values come from a stdlib transcription. The SVF is ADR 0279's recurrence in
    floats, as in its generator, and the envelope is ADR 0238's recurrence in exact rationals,
    rounded once.
  - The tolerance is `abs 1e-13, rel 1e-10`.
- The output level depends on the band count and the overlap that `q` sets. Callers normalize
  it if they need to.
