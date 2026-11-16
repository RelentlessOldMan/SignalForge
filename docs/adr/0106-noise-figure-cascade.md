# ADR 0106: Cascaded noise figure (Friis)

Status: accepted, 2026-11-16. Completes the second-stage correction that
[ADR 0105](0105-noise-figure-y-factor.md) left out.

## Context

A receiver chain is a series of stages: a cable, an LNA, a mixer and so on. Each stage has its
own noise figure and gain. Friis' formula gives the noise factor of the whole chain. It is used
to budget a design and to remove the meter's own noise from a measurement.

## Decision

- Python `noise_figure_cascade(noise_figures_db, gains_db)`, and C#
  `Measurements.NoiseFigureCascade(noiseFiguresDb, gainsDb)`. Each takes one value per stage,
  in chain order, in dB. dB is used because that is how datasheets give both quantities.
- The formula, with `Fᵢ = 10^(NFᵢ/10)`, `Gᵢ = 10^(gᵢ/10)` and `Πᵢ = G₁…Gᵢ₋₁` (with `Π₁ = 1`):
  - Each stage's contribution is `c₁ = F₁` and `cᵢ = (Fᵢ − 1)/Πᵢ`.
  - The noise factor is `F = Σ cᵢ`, added in chain order.
  - The products `Πᵢ` are multiplied in order.
  - The last stage's gain does not change `F`.
- The result is `CascadeNoiseFigure`, with these fields:
  - `noise_factor`, `F`
  - `noise_figure_db`, `10·log10 F`
  - `noise_temperature`, `T₀(F − 1)` with `T₀ = 290 K`
  - `gain_db`, the sum of the `gᵢ` in order
  - `contributions`, the `cᵢ`, so a budget can show which stage costs the most
- Arguments:
  - Both arguments are one-dimensional, the same length, at least one stage, with every value
    finite.
  - Every `NFᵢ ≥ 0`, because a stage with `F < 1` is not physical.
  - Gains may be negative. A loss is a stage like any other, and a matched loss at `T₀` has
    `NF = −g`.
  - When `F` comes out not finite, the call is `invalid_argument`. That happens when the gains
    before a noisy stage underflow to zero.
- The formula assumes the stages are matched, and its gains are available gains. Mismatch and
  stages at temperatures other than `T₀` are not modelled.

## Consequences

- Expected values are hand derivations:
  - A single stage returns itself.
  - Stages whose dB values are whole multiples of 10 give exact rationals.
  - The textbook LNA-and-mixer chain is included.
  - A matched loss `L` in front of an amplifier gives `F = L·F₂`, so 6 dB before 2 dB gives 8 dB.
- The first `contributions` entry is at least 1, and the others are each non-negative.
