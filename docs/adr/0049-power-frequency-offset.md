# ADR 0049: Coarse frequency offset from the power spectrum of zᵖ

Status: accepted, 2026-11-13

## Context

The link's coarse carrier estimate, `qpsk_frequency_offset`, is the mean phase step of `z⁴` from
one symbol to the next. On QPSK `z⁴` is a constant times a tone, so that works. On 16-QAM `z⁴`
has a mean of −0.68 but an rms of about 1.6 about it, and the product of two neighbours has a mean
of 0.46 against an rms of about 3: on 400 noiseless 16-QAM symbols at 1000 Bd the estimate was
off by 9 Hz rms (prototype, 40 trials), and the link's block-phase line then aliased.

## Decision

- A new estimator, `power_frequency_offset(symbols, symbol_rate, power)`: the peak of the
  periodogram of `zᵖ` (a zero-padded FFT, at least 4 points per symbol), refined by bisection on
  the sign of the periodogram's slope (conventions: Synchronization). It sums the line coherently
  over the block, so the self-noise grows as `√N` against the line's `N`. In the prototype it
  was 0.018 Hz rms on the same 400 noiseless symbols, and 0.03 Hz at Eb/N0 8 dB.
- The power is an argument, so the same function serves 16-QAM (4) and 8-PSK (8).
- Bisection on the slope's sign, with a fixed 60 steps, ends at the same point in both languages
  to rounding, where a golden-section search on the flat top of the peak would not.
- `qpsk_frequency_offset` stays as it is, and so do the QPSK link and its reports. Moving the
  QPSK link to the new estimator is a separate choice.

## Consequences

- Cost is one FFT of `4N` to `8N` points plus 60 passes over the block, against one pass.
- Below a few dozen symbols the estimate can lock onto a noise peak (64 symbols of 16-QAM at
  8 dB: 62 Hz rms in the prototype); the link should estimate over the whole frame.
