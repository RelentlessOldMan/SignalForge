# ADR 0028: Group delay

Status: accepted, 2026-11-13

## Context

Group delay is the derivative of the phase. Computing it by unwrapping a sampled phase and
differencing depends on the frequency spacing and breaks at phase jumps, so two implementations
would not agree. The choices: units, sign, how it is computed, and what to return where `H` has a
zero on the unit circle (the phase jumps by π there and the derivative does not exist).

## Decision

- **`fir_group_delay(taps, frequencies, sample_rate)` and `sos_group_delay(sos, frequencies,
  sample_rate)`**, beside `fir_response` and `sos_response`, with the same arguments.
- **Samples, positive for a delay**: `τ = −dφ/dω` with `ω = 2πf/fs`. Divide by `fs` for seconds.
- **Closed form per polynomial**: `τ_P = Re(R/P)` with `R = Σ n·c_n·e^(−jωn)`, the exact
  derivative of `arg P`. Sections add: `τ = Σ (τ_B − τ_A)`, so a cascade needs no polynomial
  multiplication and no root finding.
- **NaN where a polynomial is within rounding of 0**: `|P| ≤ 1e-10·Σ|c_n|`. A zero exactly on the
  unit circle has a limit there for its neighbours (each contributes ½ sample away from its
  angle), but at the zero itself the phase jumps and no value is right; NaN says so instead of
  returning a large rounding artefact that the two languages would not share.

## Consequences

- Near (but not within 1e-10 of) a zero on the unit circle the result is large and sensitive to
  rounding, so vectors keep away from such points except for the NaN cases themselves.
- Expected values come from a different formula: a sum over chosen roots of the closed-form
  delay of each first-order factor, `Re(−q·e^(−jω)/(1 − q·e^(−jω)))`, plus by-hand cases.
