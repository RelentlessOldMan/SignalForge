# Testing and cross-language validation

## Three layers

1. **Unit tests per language** (`python/tests`, `dotnet/tests`): behaviour, edge cases, errors,
   properties (a PRBS has period `2ᵐ−1` and `2ᵐ⁻¹` ones; a demapped map returns the input bits).
2. **Shared vectors** (`vectors/cases/*.json`): language-neutral cases with expected results. Both
   test suites load every file and run every case. This is the cross-language contract.
3. **Cross-generation** (planned, Phase 3): Python generates a signal file, C# analyses it, and the
   other way round; a tool compares both languages' reports and lists discrepancies.

## Where expected values come from

An expected value in `vectors/` must come from something **other than** the code under test:

- an analytical result (`10·log10(1000) = 30`, the samples of `e^{jπn/4}`),
- a derivation by hand written into the case's `source` field (the first bits of PRBS7),
- a published example, cited, or
- an independent, approved third-party implementation, named.

Never generate expected values by running SignalForge and pasting the output: a bug shared by both
languages would then pass. If a case's value was produced by a tool, `source` says which.

## Vector format

See [`vectors/README.md`](../vectors/README.md).

## Tolerances

Each case gives `abs` and/or `rel`; a value passes when `|actual − expected| ≤ abs + rel·|expected|`.
Default when a case gives none: `abs = 1e-12, rel = 1e-12`. Rules of thumb:

- Closed-form double-precision arithmetic (unit conversions): 1e-12.
- Trig of arguments up to ~1e4 rad: 1e-12 absolute on unit-amplitude samples.
- Sums over N samples: allow ~N·1e-16 relative.
- Anything involving an FFT, a filter, or an estimator: set per case from the algorithm's error
  analysis, and write down why in `source`.

## Random signals

Seeds are explicit everywhere. Python and C# generators differ, so cross-language checks on noise
compare statistics with tolerances derived from the sample size, or exchange the samples as files.

## Running

See the Commands section of `CLAUDE.md`.
