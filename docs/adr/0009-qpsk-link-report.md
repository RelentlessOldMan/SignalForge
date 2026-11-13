# 0009: End-to-end QPSK link and its JSON report

Date: 2026-11-13. Status: accepted.

## Context

The QPSK slice ends with one call that runs bits → shaping → channel → recovery → EVM/BER and returns
a result a script can store and compare. It needs a public shape (what goes in, what comes out), a
JSON form both languages write alike, and a receiver defined tightly enough that both languages
make the same decisions.

While building it, the block estimators of ADR 0008 turned out not to be enough on their own. At
6 dB Eb/N0 the lag-1 fourth-power frequency estimate is off by 0.1 to 0.5 Hz at Rs = 1000, whether
the frame has 2000 symbols or 100k. A frame of N symbols then turns by `2π·δf·N/Rs`, which is whole
turns, and BER came out 200 times theory.

## Decision

- A new module `link` (`signalforge.link` / `SignalForge.Link`) with one function,
  `qpsk_link(config) -> QpskLinkReport`. Its input is a record, `QpskLinkConfig`, and the report
  carries that config, so a report describes its own run.
- The report holds the receiver's estimates (timing offset, frame start, frequency, phase) and the
  existing `Evm` and `ErrorCount` records, plus the theoretical BER (`None`/`null` without noise).
- JSON: the record's fields, nested, with the same snake_case names in both languages (C# maps its
  PascalCase through `System.Text.Json`, which is part of .NET itself, not a package). Non-finite
  numbers are written as the strings `"inf"`, `"-inf"` and `"nan"`, as in the vectors, so the output
  is strict JSON. Two reports are compared as JSON values, not as text: `6.0` and `6` are the same.
- The receiver is the ADR 0008 estimators plus two steps, all feed-forward:
  - a **preamble search** for the frame start: the first `preamble_symbols` symbols are known, and
    the frame starts at the first maximum of the correlation magnitude;
  - **fine frequency and phase from block phases**: `qpsk_block_phases` (new, in `sync`) gives the
    fourth-power phase of each block of symbols, unwrapped in steps of π/2, and a least-squares line
    through those phases gives the residual frequency (slope) and the phase at the frame start
    (intercept). The preamble then resolves the π/2 ambiguity.
  The exact steps are in `docs/conventions.md` (QPSK link).

## Consequences

- At 6 dB, BER matches theory within the run's own scatter for frames of 2000 to 100k symbols, and
  the fine frequency error falls to about 1e-6 Hz on 100k symbols.
- Unwrapping needs the coarse frequency error below `Rs/(8·block)` (3.9 Hz with the default 32-symbol
  blocks at Rs = 1000); the coarse estimator's own range is ±Rs/8. A frame with drift or phase noise
  needs the tracking loops that come later.
- The channel's offset is applied before the matched filter, so a large offset (10% of Rs) leaves
  some inter-symbol interference: that is the physics of the link, not an estimator error.
- Random streams differ between languages, so noisy runs are compared by statistics. Noiseless runs
  are deterministic, so their vectors check the whole chain in both languages against the channel's
  own parameters.
