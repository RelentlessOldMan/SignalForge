# ADR 0050: 16-QAM in the link

Status: accepted, 2026-11-13

## Context

The link runs QPSK only. 16-QAM has a mapper, demappers, a carrier loop, a BER theory and, since
ADR 0049, a coarse frequency estimator that works on it. Its fourth power has a negative real
mean like QPSK's, so the link's block phase estimates and their π/2 ambiguity work unchanged.

## Decision

- A config field `modulation`, `"qpsk"` (the default, so existing configs and reports stay the
  same) or `"qam16"`: the names are the functions' prefixes. 8-PSK needs eighth-power estimators
  and is a later value of the same field.
- Eb/N0 is per information bit for each: the AWGN Es/N0 is `eb_n0_db + 10·log10 k`.
- The mapper, the coarse frequency estimate (`power_frequency_offset(·, Rs, 4)` for 16-QAM), the
  carrier loop's decision, the demapper and the theory follow the field; the rest of the chain is
  shared. QPSK keeps `qpsk_frequency_offset`, so its reports do not change. The record and its JSON stay `QpskLinkConfig` / `QpskLinkReport` for
  now; renaming them is a breaking change for a later, wider link API.

## Consequences

- With 16-QAM the preamble correlation and the block phase estimates are noisier for the same
  Eb/N0 than with QPSK (the inner points carry less energy), so a 16-QAM config wants more
  preamble symbols at low Eb/N0.
