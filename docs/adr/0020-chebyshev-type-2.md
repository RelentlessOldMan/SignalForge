# 0020: Chebyshev type II IIR design

Date: 2026-11-13. Status: accepted.

## Context

A Chebyshev type II (inverse Chebyshev) filter is flat in the pass band, like Butterworth, and
puts its ripple in the stop band, with zeros on the unit circle. It is the usual choice when a
minimum stop-band attenuation is the requirement. Choices: what the cutoff means, how the
attenuation is given, how zeros pair with poles, and the gain.

## Decision

- **Low-pass and high-pass**, `chebyshev2_lowpass(order, attenuation_db, cutoff, sample_rate)`
  and `chebyshev2_highpass(...)`, by the same prewarped bilinear transform as Butterworth and
  type I, so `|H|²` has the closed form `ε²T_N²/(1 + ε²T_N²)` in `K/t` (or `t/K`).
- **The cutoff is the stop-band edge**, where the response first reaches `−attenuation_db`. This
  is the defining frequency of the type II prototype and the usual definition for the family; the
  −3 dB point lies inside the pass band.
- **The attenuation is the stop band's peak level**, in dB of power, positive, at most 200 dB
  (as for the type I ripple, beyond that the design has no meaning in double precision).
- **Pairing**: pole pair `k` (the reciprocal of type I's pair `k`) takes the zeros at
  `±j/sin θ_k`. That puts the highest-Q pair with the zeros nearest the stop-band edge, the usual
  nearest-zero pairing for this family, and the sections keep Butterworth's order. The shared
  cascade builder takes the zeros as an extra input; with none it gives Butterworth's zeros.
- **Unit gain** per section at DC (low-pass) or `fs/2` (high-pass): the type II response is
  exactly 1 there for every order.
- Implemented from the definitions; no third-party code.

## Consequences

- The generator builds each section from the analog quadratics (`s² + Ω²` over
  `s² − 2σs + M`) through the bilinear transform, and checks every design against the closed
  form and for stability before writing it.
- Band forms and elliptic designs are later work.
