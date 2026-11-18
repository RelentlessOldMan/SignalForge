# ADR 0327: Allan deviation

Status: accepted, 2026-11-18.

## Context

An oscillator's frequency stability over an averaging time `τ` is given by the Allan
deviation, not the standard deviation, which does not converge for the flicker and random-walk
noises clocks have. The overlapping estimator uses every start instead of only disjoint
blocks, so it has more degrees of freedom from the same record. The definitions follow the
usual time-and-frequency literature (for example NIST Special Publication 1065).

## Decision

- **The API.**
  - Python: `allan_deviation(fractional_frequency, sample_interval, averaging_factors)` in
    `measurements`, giving `AllanDeviation(taus, deviations)`, two float arrays.
  - C#: `Measurements.AllanDeviation(ReadOnlySpan<double> fractionalFrequency,
    double sampleInterval, ReadOnlySpan<int> averagingFactors)`, giving the record
    `AllanDeviation(double[] Taus, double[] Deviations)`.
- **The value.**
  - `y[i]`, `i = 0 … M−1`, are fractional-frequency samples `(f − f₀)/f₀`, each the mean over
    one `sample_interval` `τ₀`.
  - For each averaging factor `m`, in the order given:
    - `ȳ_k = (1/m)·Σ_{i=k}^{k+m−1} y[i]`, `k = 0 … M−m`. Each mean is summed directly, not
      from a running sum, so its error is a rounding of that mean, not of a sum over the whole
      record.
    - `σ² = Σ_{j=0}^{M−2m} (ȳ_{j+m} − ȳ_j)² / (2·(M − 2m + 1))`.
    - `τ = m·τ₀` and the deviation is `sqrt(σ²)`.
- **The rules.**
  - `fractional_frequency` real, one-dimensional and finite, at least 2 long.
  - `sample_interval` finite and positive.
  - `averaging_factors` non-empty integers, each at least 1 with `2m ≤ M`. Repeats and any
    order are allowed.

## Consequences

- **Checks.** A linear frequency drift `y = D·i·τ₀` gives exactly `σ = D·τ/√2`, and white
  frequency noise of variance `s²` gives `σ² ≈ s²/m`. The tests use both.
- **Vectors.**
  - The samples are dyadic. The generator computes `σ²` exactly in rationals and takes one
    float square root.
  - The tolerance is `abs 1e-15, rel 1e-12`. One case has an offset of 1 under a wander of
    about 1e-9. There the means round at about 1e-16, which the absolute tolerance covers;
    a relative one could not.
