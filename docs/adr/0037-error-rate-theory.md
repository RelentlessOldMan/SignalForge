# ADR 0037: Error-rate theory for 16-QAM and 8-PSK

Status: accepted, 2026-11-13

## Context

`qpsk_ber_theory` is the only theory curve. With 8-PSK and 16-QAM mapped (ADR 0035), a link or a
test needs their bit and symbol error rates in AWGN. Textbooks give several forms: the
nearest-neighbor approximations (`Pb ≈ Ps/k`, `Ps ≈ 2Q(√(2Es/N0)·sin(π/M))`), the exact
square-QAM symbol rate, and for M-PSK an integral with no closed form.

## Decision

- Four functions of `eb_n0_db`, named after the existing one: `qam16_ber_theory`,
  `qam16_ser_theory`, `psk8_ber_theory`, `psk8_ser_theory`.
- All four are exact for our Gray labelings, not approximations. For 16-QAM the closed forms;
  for 8-PSK the one-sided phase tail in Pawula's form, a finite integral of a smooth bounded
  integrand, by Simpson's rule on a fixed 4096 panels so both languages compute the same sum.
- No `M`-generic function yet: the mappers are specific, and so are these.

## Consequences

- Vectors come from a stdlib generator (`vectors/generators/error_rates.py`) that checks the
  16-QAM forms against integrating the Gaussian over the decision intervals, and gets 8-PSK by
  integrating the received phase's density, a form the libraries do not use.
- Monte-Carlo tests in each language check the curves against the mappers, `awgn` and the hard
  demappers.
