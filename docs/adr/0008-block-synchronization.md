# 0008: Block synchronization estimators

Date: 2026-11-13. Status: accepted.

## Context

The QPSK slice needs timing and carrier recovery that works on a captured block. The choices are
tracking loops (Gardner or Mueller–Müller timing with an interpolator, a Costas loop) or
feed-forward estimators that look at the whole block once. Loops follow drift, but have state,
gains and a transient, and are hard to give exact expected values to. Feed-forward estimators are
a single formula over the block.

## Decision

- **Feed-forward block estimators first**, in a new module `sync` (`signalforge.sync` /
  `SignalForge.Sync`), as the architecture planned for the first real recovery:
  - **timing:** the Oerder–Meyr estimator, the phase of the symbol-rate line in `|y|²`, giving a
    fractional sample offset;
  - **carrier frequency (QPSK):** the fourth power removes the modulation, and the mean phase step
    of `z⁴` between symbols gives the offset;
  - **carrier phase (QPSK):** the phase of the mean of `−z⁴`, divided by 4, with the usual π/2
    ambiguity.
- The estimators only **estimate**. Correction uses functions that already exist:
  `frequency_offset` with the negated estimates, and sampling at the rounded timing offset.
  Interpolation for fractional timing comes with the resampling work.
- Definitions are in `docs/conventions.md` (Synchronization). Each estimator is exact on a clean
  synthetic signal, so its vectors are analytical.
- Tracking loops come later, behind the same names with a `_loop` suffix, when a signal with drift
  needs them.

## Consequences

- No state, no gains to tune, and the same answer in both languages to rounding error.
- They assume a constant offset over the block. Frequency is unambiguous only within ±Rs/8 and
  phase only within ±π/4 (QPSK's fourfold symmetry); resolving the π/2 ambiguity needs known
  symbols (a preamble), which the link function will use.
