# 0025: Bessel IIR design

Date: 2026-11-13. Status: accepted.

## Context

A Bessel (Thomson) filter has a maximally flat group delay, so it keeps the shape of pulses that
fit in its pass band; it is the usual choice in front of a decision or a measurement of a
waveform's timing. The analog prototype is defined by the reverse Bessel polynomial, but there
are three common normalizations, and they put the "cutoff" at different places: unit group delay
at DC, phase matched to the Butterworth's at high frequency, or −3 dB at the cutoff. The roots of
the polynomial also lose accuracy quickly with the order.

## Decision

- **Low-pass and high-pass**, `bessel_lowpass(order, cutoff, sample_rate)` and
  `bessel_highpass(...)`, by the same prewarped bilinear transform as the other IIR designs.
- **The cutoff is the −3 dB point.** This is the only normalization that means the same thing for
  every family here (Butterworth's cutoff is −3 dB too), and with prewarping it holds exactly in
  the digital filter. The delay and phase normalizations differ only by a factor on the prototype
  frequency; they can be had by scaling the cutoff, and are not separate functions.
- **The order is at most 10.** Measured against 60-digit roots, the double-precision roots of the
  reverse Bessel polynomial hold about 7e-13 relative at order 10, 9e-10 at 15, 3e-4 at 25 and
  nothing at 30, by the coefficients or by the three-term recurrence alike. An order of 10 already
  gives more selectivity than a Bessel filter is chosen for; higher orders would return poles
  that two correct implementations need not agree on.
- **Roots by Aberth's iteration** evaluating the polynomial by its recurrence, then a Newton
  step; any method converging to double precision agrees to rounding, so the method is not part
  of the convention. The same for `ω₀`, the unique positive root of `|θ_N(jω)|² = 2θ_N(0)²`.
- **Sections** in the Butterworth order (rising Q), with the Butterworth zeros and unit gain at
  DC or `fs/2`: Bessel's DC gain is exactly 1.
- **The bilinear transform is kept** although it bends the group delay at high cutoffs; an
  impulse-invariant or matched-z design would keep more of the delay but loses the exact −3 dB
  point and is a different family of methods. The conventions say where the delay stays flat.
- Implemented from the definitions; no third-party code.

## Consequences

- Expected values: order 1 and 2 by hand (`θ_2 = s² + 3s + 3`, `ω₀² = 3(√5 − 1)/2`), and a
  generator that finds the roots from the exact integer coefficients in 50-digit arithmetic, `ω₀`
  by bisection on the exact `|θ_N(jω)|²` polynomial, and builds each section from its real
  quadratic; each design is checked against the closed-form `|H|²` and for stability.
- Bessel band-pass and band-stop are not built: the low-pass-to-band transform does not keep the
  flat delay, so they are rarely wanted.
