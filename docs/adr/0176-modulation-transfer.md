# ADR 0176: Modulation transfer function

Status: accepted, 2026-11-16. It builds on the ISO 3382 energy measures in ADRs 0171 to 0175,
and is the input to a speech transmission index.

## Context

Schroeder showed that the modulation transfer function of a linear room follows from its impulse
response:

    m(F) = |Σ h²(t)·e^{−j2πFt}| / Σ h²(t)

`m(F)` is the factor by which an intensity modulation at `F` Hz survives the room. Implementations
differ on three points:

- the time origin;
- the sign of the exponent;
- whether frequencies above `fs/2` are allowed.

## Decision

- **The API.** In `measurements`, for real and complex input:
  - Python: `modulation_transfer(impulse_response, sample_rate, frequencies)`.
  - C#: `Measurements.ModulationTransfer(impulseResponse, sampleRate, frequencies)`.
  - Both return one `m` per frequency, in order.
- **The definition.** `m(F) = |Σ_n |h[n]|²·e^{−j2πF n/fs}| / Σ_n |h[n]|²`.
  - The origin is index 0, as in ADR 0172.
  - The phase is computed as `2π·F·n/fs` in double, with no reduction.
  - The sign of the exponent does not change `|·|`; minus is written for definiteness.
- **The frequencies.** Each is finite and `≥ 0`. A frequency above `fs/2` is allowed and aliases
  as the formula says. `F = 0` gives 1.
- **The rules.**
  - The response is one-dimensional, finite, not empty and not all zero.
  - `frequencies` is one-dimensional and not empty.
  - `sample_rate` is finite and positive.
  - Anything else is `invalid_argument`.

## Consequences

- **The STI is not here.** A speech transmission index needs the octave-band MTFs, the band
  weights and the masking corrections from IEC 60268-16. That is a later slice, and its
  tables need their own check.
- **Vectors are closed forms and hand sums.**
  - For `h[n] = r^n` over `L` samples, `m(F) = |(1 − (q z)^L)/(1 − q z)| / ((1 − q^L)/(1 − q))`,
    with `q = r²` and `z = e^{−j2πF/fs}`. This is evaluated with `cmath`, which is independent
    of the direct sum the implementations do.
  - Hand cases have exact values: `[1, 1]` at `F = fs/4` gives `√2/2`, and at `F = fs/2` it
    gives 0.
- **A test checks the continuous form.** It confirms Schroeder's
  `1/√(1 + (2πF·T/(6 ln 10))²)` for a long decay, at 0.1 % (the textbook 13.8 is 6 ln 10 rounded).
