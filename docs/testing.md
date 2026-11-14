# Testing and cross-language validation

## Three layers

1. **Unit tests per language** (`python/tests`, `dotnet/tests`): behaviour, edge cases, errors,
   properties (a PRBS has period `2ᵐ−1` and `2ᵐ⁻¹` ones; a demapped map returns the input bits).
2. **Shared vectors** (`vectors/cases/*.json`): language-neutral cases with expected results. Both
   test suites load every file and run every case. This is the cross-language contract.
3. **Cross-language checks** (`python -m signalforge.compare`, run by `build.ps1` and CI): the
   two languages' results compared with each other, below, including signal files written by each
   language and read by both.

## Where expected values come from

An expected value in `vectors/` must come from something **other than** the code under test:

- an analytical result (`10·log10(1000) = 30`, the samples of `e^{jπn/4}`),
- a derivation by hand written into the case's `source` field (the first bits of PRBS7),
- a published example, cited, or
- an independent, approved third-party implementation, named.

Never generate expected values by running SignalForge and pasting the output: a bug shared by both
languages would then pass. If a case's value was produced by a tool, `source` says which.
Scripts that compute a whole vector file live in `vectors/generators/`: Python standard library
only (never NumPy or SignalForge), by a different method from the library where there is one (the
FIR taps integrate the ideal spectrum numerically instead of using the sinc closed form). CI runs
each with `--check` so a file can't drift from its generator.

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
- Monte Carlo BER tests in the unit suites bracket the rate between theory and theory with the
  known losses taken out of Eb/N₀ (a channel estimate from `P` blocks costs `10·log10(1 + 1/P)` dB),
  widened by 4 binomial standard deviations. Where a loss has no closed form (the OFDM tracking
  loops' jitter and the leakage a clock offset or phase noise causes between subcarriers), the
  test adds a fixed allowance in dB, named as an allowance in the test (0.5 dB for ADR 0065), not
  a derived value.

## Random signals

Seeds are explicit everywhere. Python and C# generators differ, so cross-language checks on noise
compare statistics with tolerances derived from the sample size, or exchange the samples as files.

## Cross-language checks

Passing the same vectors is not quite agreeing: a case lists only the fields it checks, and two
results can each be within tolerance of the expected value on opposite sides. So both runners
write a report of every case's actual result (`reports/python.json` from
`python -m signalforge.conformance --report`, `reports/dotnet.json` from the C# tool
`dotnet/tools/SignalForge.Conformance --report`), and `python -m signalforge.compare reports`
diffs them:

- every case is in both reports and in `vectors/cases`, and passes or fails in both;
- the two actual results have the same fields, at every depth, and agree within the case's own
  tolerance.

A record's fields are its public properties in C# and its dataclass fields plus public properties
in Python, so a computed field such as `SpectralDensity.span` is compared too.

The link compare (`python -m signalforge.compare link A.json B.json`) takes two `qpsk_link`
reports of one config. Each config in `vectors/links/` is run in both languages
(`compare run-link` and the C# tool's `link`) and the reports compared:

- both reports have the same fields, and the configs are equal;
- without noise the runs are deterministic, and every field must agree within 1e-9 (absolute plus
  relative), except that when both EVMs have `rms ≤ 1e-9` (an exact recovery, as OFDM gives)
  their `rms_db` and `peak_index` are not compared: they describe rounding error;
- with noise the random streams differ, so the frame start, the bit count and the symbol count
  must be equal, and two statistics must agree within 4 standard deviations:
  - bit errors, a two-sample test of proportions: `|e₁ − e₂| ≤ 4·√(2·n·p·(1 − p))`, `p` the pooled
    rate over `n` bits each;
  - mean squared EVM: `|e₁² − e₂²| ≤ 4·m̄·√(2/N)`, `m̄` their mean, over `N` symbols each (the
    squared magnitude of complex Gaussian error is exponential, so its standard deviation equals
    its mean).
  The theoretical BER depends only on the config and must agree within 1e-9. The receiver's
  estimates (timing, frequency, phase) are noisy and are not judged. FSK reports have no EVM
  (both must say `null`, and the EVM test is skipped). Nor is the EVM tested for a noisy config
  with multipath: after equalization it is a mean of per-subcarrier parts of very different size,
  led by the weakest subcarriers and their channel estimates, so no per-symbol standard deviation
  fits it (a 19 sd difference in testing); the BER test still applies. An FSK receiver may land on `delay` or
  `delay + 1` equally well, so noisy FSK configs keep `delay_samples mod sps < sps − 1`, where
  both give the same frame start.

The file exchange: each language writes one recording per datatype into one directory
(`compare write-files` and the C# tool's `write-files`; 64 samples of a raised-cosine-shaped tone,
the same formula in both, with units, impedance, time origin, center frequency and metadata). Each
language reads every recording there into a report (`read-files`), and `compare files` checks:

- both reports read the same recordings, and every value agrees exactly (both decode the same
  bytes);
- for each datatype, the Python and C# recordings agree in every field and in their metadata
  (except `writer`), and their samples within one quantization step plus 1e-12 (the formula's
  rounding may differ by an ulp between the languages).

## Running

See the Commands section of `CLAUDE.md`.
