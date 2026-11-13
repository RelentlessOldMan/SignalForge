# ADR 0036: Phase noise

Status: accepted, 2026-11-13

## Context

A free-running oscillator's phase drifts. The simplest model that has the right spectrum near
the carrier is the Wiener process: the phase is a random walk, and the carrier's spectrum is a
Lorentzian whose full 3 dB width is the linewidth. Implementations differ on what sets the
size of the steps (linewidth, a PSD level at an offset, or the step's standard deviation) and on
where the walk starts.

## Decision

- `phase_noise(samples, linewidth_hz, sample_rate, *, seed)`: `φ[0] = 0`, increments
  independent Gaussian with variance `2π·linewidth_hz/sample_rate`, `y = x·e^{jφ}`.
- The argument is the linewidth because it is what a datasheet or a laser gives, and it fixes
  the Wiener model completely.
- Seeded like `awgn` (an integer or a generator in Python; an integer or a `Random` in C#).

## Consequences

- The streams differ between languages, so the vectors only hold what is not random (a zero
  linewidth, a single sample, the errors); the unit tests in each language check the statistics
  against theory: the increment variance, the variance over a lag, and the mean
  `E[e^{jφ[n]}] = e^{−nσ²/2}`.
- A phase-noise mask (a PSD given at offsets, with a flat floor) is a later model; this one has
  no floor and its PSD falls as `1/f²` for ever.
