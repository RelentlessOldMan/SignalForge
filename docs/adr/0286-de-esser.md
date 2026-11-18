# ADR 0286: De-esser

Status: accepted, 2026-11-17.

## Context

A de-esser turns a voice down while it is sibilant: the "s" and "sh" sounds, a narrow band of
energy around 5 to 8 kHz. It is a sidechain compressor (ADR 0278) keyed on that band of the
voice itself. The band is the state-variable band-pass (ADR 0279), scaled to unity peak gain so
the threshold reads as the level of the sibilant band.

## Decision

- **The API.**
  - Python: `de_esser(samples, cutoff, q, threshold_db, ratio, attack, release, sample_rate)`
    in `dsp`.
  - C#: `Dsp.DeEsser(samples, cutoff, q, thresholdDb, ratio, attack, release, sampleRate)`.
  - Real samples only.
- **The value.**
  - The key is `(1/q)·svf(samples, cutoff, q, fs, output="bandpass")`, element by element.
  - The output is `duck(samples, key, threshold_db, ratio, attack, release)`: a hard knee and
    no make-up gain.
  - The whole signal is turned down, not only the band. A split-band de-esser can be built
    from `crossover_split` later.
- **The rules.**
  - The SVF's rules for `cutoff`, `q` and `fs`.
  - The sidechain compressor's rules for `threshold_db`, `ratio`, `attack` and `release`.
  - The samples must be real, finite and at least one.

## Consequences

- **Vectors.**
  - Expected values come from a stdlib transcription. The SVF runs in floats, and the key is
    checked against `1/q` times the direct-form band-pass of ADR 0279 in exact rationals. The
    envelope is computed in exact rationals, and the level, the gain and the factor come from
    floats, as in ADR 0278.
  - The tolerance is `abs 1e-14, rel 1e-11`. The key feeds a logarithm.
