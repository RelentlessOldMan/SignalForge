# ADR 0048: Carrier loops for 8-PSK and 16-QAM

Status: accepted, 2026-11-13

## Context

`qpsk_carrier_tracking` follows the carrier phase on QPSK symbols. 8-PSK and 16-QAM have mappers
and demappers but no loop.

## Decision

- `psk8_carrier_tracking` and `qam16_carrier_tracking`, with the arguments and result of the QPSK
  loop, one function per modulation as the mappers are. Only the decision changes; the detector
  `Im{conj(d)·r}` and the PI update are shared code in each language.
- The decision is the hard demapper's, written out in the conventions: the 8-PSK sector by the
  demapper's rounding, the 16-QAM level by its threshold. The 8-PSK points use `1/√2` for the
  diagonal coordinates rather than `cos(π/4)`, so both languages compute the same detector.
- The decision point is the constellation point itself (unit average energy), so the 8-PSK
  detector has slope `|z|` and the 16-QAM detector a mean slope of `|z|`'s scale.

## Consequences

- 8-PSK locks to multiples of π/4, 16-QAM to multiples of π/2: the caller resolves them, as for
  QPSK.
- Decision-directed 16-QAM pulls in only from within about ±π/8 of lock (the inner and outer
  points disagree beyond that); a wider pull-in needs a training sequence or a different detector,
  later.
