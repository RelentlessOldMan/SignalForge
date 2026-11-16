# ADR 0179: Stage support

Status: accepted, 2026-11-16. It goes with the ISO 3382 parameters in ADRs 0171 to 0178.

## Context

ISO 3382-1 Annex C measures how well performers on a stage hear each other. It uses the
reflected energy relative to the direct sound, from a response taken 1 m from the source:

- `ST_early = 10·log10(E_{20–100 ms} / E_{0–10 ms})`;
- `ST_late = 10·log10(E_{100–1000 ms} / E_{0–10 ms})`.

Implementations differ on three points:

- how the window bounds round;
- what a window that runs past the end gives;
- what silence gives.

## Decision

- **The API.** In `measurements`, for real and complex input:
  - Python: `stage_support(impulse_response, sample_rate, *, late=False)`.
  - C#: `Measurements.StageSupport(impulseResponse, sampleRate, late = false)`.
  - The result is in dB.
- **The windows.**
  - Each bound `t` becomes `N(t) = ⌊t·fs + 1/2⌋`, the rounding of ADR 0172.
  - The windows are half-open: the direct sound is `[0, N(0.01))`, the early window
    `[N(0.02), N(0.1))` and the late window `[N(0.1), N(1))`.
  - Index 0 is the direct sound.
  - Windows past the end are clipped, so a response shorter than 1 s gives the late energy it
    has.
- **The results.**
  - A silent reflection window gives `−inf`.
  - `N(0.01) ≥ 1` is required, which needs `fs ≥ 50` Hz.
  - A silent direct window is `invalid_argument`.
- **The rules.**
  - The response is one-dimensional, finite and not empty.
  - `sample_rate` is finite and positive.
  - Anything else is `invalid_argument`.

## Consequences

- **The caller's job.** Trimming the response so that the direct sound is at index 0 is the
  caller's job, as in ADR 0172.
- **Vectors.** They are exact hand sums at 100 Hz, where the bounds are 1, 2, 10 and
  100 samples, and geometric window sums `(q^a − q^b)/(1 − q)` at 1 kHz, in 50-digit `decimal`.
