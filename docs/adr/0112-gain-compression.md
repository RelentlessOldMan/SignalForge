# ADR 0112: Gain compression (P1dB)

Status: accepted, 2026-11-16.

## Context

An amplifier's gain falls as the drive rises. The 1 dB compression point, P1dB, is the drive
at which the gain is 1 dB below its small-signal value. It is quoted next to IP3 (ADR 0107) and
IP2 (ADR 0110). It comes from a power sweep: one input level and one output level per step, read
from a power meter, a spectrum analyser, or `tone_metrics` on captured samples.

## Decision

- Python `gain_compression(input_db, output_db, *, compression_db=1.0, linear_points=1)`, and
  C# `Measurements.GainCompression(...)`.
  - The inputs are a sweep's levels in dB of one unit, for example dBm, or the dB of a tone
    amplitude. Taking levels rather than samples keeps the call independent of how they were
    measured.
- **Arguments.**
  - `input_db` and `output_db` are 1-D, the same length, at least 2, and finite.
  - `input_db` must be strictly ascending.
  - `compression_db` is finite and `> 0`.
  - `linear_points` is a whole number from 1 to the sweep's length.
- **Gain.** At each step the gain is `gᵢ = outᵢ − inᵢ`.
  - The small-signal gain `G` is the mean of the first `linear_points` gains, summed in order.
    The default is the lowest drive alone. More points average out a noisy reading.
- **Compression.** At each step the compression is `cᵢ = G − gᵢ`. Expansion makes it negative.
- **The compression point.**
  - The point is the first step `k` with `c_k ≥ compression_db`. Between steps `k − 1` and `k`,
    the input point is interpolated linearly in dB:
    `in_{k−1} + (compression_db − c_{k−1})/(c_k − c_{k−1})·(in_k − in_{k−1})`.
  - If `k = 0`, the input point is `in₀`.
  - If no step reaches it, the point is NaN. The sweep did not drive far enough, which is a
    result, not an error.
  - The output point is `input point + G − compression_db`. That is the output level there, on
    the interpolated gain.
- **Saturation.** The saturated output is the largest `outᵢ`.
- **The result** is `GainCompression`. It has:
  - `small_signal_gain_db`
  - `gain_db` and `compression`, one value per step
  - `input_point_db` and `output_point_db`
  - `saturated_output_db`

## Consequences

- **Vectors.** These are worked by hand.
  - A piecewise sweep, flat and then compressing in whole and half dB, puts the points on round
    numbers.
  - The cubic `y = a₁x + a₃x³` on a tone has fundamental amplitude `a₁A + ¾a₃A³`. Its sweep
    levels are written from that formula.
- **Tests.** A fine cubic sweep finds the textbook point
  `A² = (4/3)(1 − 10^(−1/20))|a₁/a₃|`. Shifting every output by a constant moves `G` and the
  output point by that constant, and leaves the input point where it is.
