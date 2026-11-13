# ADR 0039: Soft demapping

Status: accepted, 2026-11-13

## Context

A soft-decision decoder wants a log-likelihood ratio per bit, not a hard bit. Implementations
differ on the sign (bit 0 or bit 1 positive), on whether they compute the exact log-sum or the
max-log approximation, and on what "noise variance" means (per real dimension, or `N0` for the
complex noise).

## Decision

- `qpsk_demap_llr`, `psk8_demap_llr`, `qam16_demap_llr`, each `(symbols, noise_variance)`,
  returning one real LLR per bit in the same order as the hard demappers.
- **Max-log**, by a search over every constellation point: the usual receiver choice, it needs no
  exponentials, and it scales with the noise variance exactly, so a decoder that ignores scale
  loses nothing.
- **Positive means bit 0**, `LLR = ln P(b=0)/P(b=1)`, the most common sign in coding texts; with
  our mappings bit 0 is the positive side, so for QPSK the LLR has the sign of the component.
- `noise_variance` is `N0 = E|n|²`, what `awgn` adds per complex sample at one sample per symbol.

## Consequences

- An exact log-sum demapper is a later addition if a decoder needs it; the conventions state the
  bound between the two (`ln(M/2)`), which the tests check.
- The search is over 4, 8 or 16 points per symbol; fast enough for the sizes the tests and links
  use.
