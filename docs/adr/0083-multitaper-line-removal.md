# ADR 0083: Multitaper line removal

Status: accepted, 2026-11-13

## Context

A strong line makes a multitaper PSD show a plateau `2W` wide around it, and a line's power is
not a density, so it distorts the band either way. Thomson (1982) reshapes the spectrum by taking
the lines the harmonic F-test (ADR 0080) finds and subtracting each one's fitted contribution
`μ·V_k(f − f₀)` from every eigencoefficient. Then he estimates the continuous part from what
remains, and reports the lines separately.

The subtraction can be done from the samples. `V_k(f − f₀)` is the DFT of `v_k[n]·e^{2πi f₀ n/fs}`,
so subtracting it from every `X_k` at every bin gives the tapered DFTs of
`x[n] − μ·e^{2πi f₀ n/fs}`. Removing the line from the data and running `multitaper_psd` again
gives exactly the reshaped spectrum, with every option the PSD has (one-sided, padding,
adaptive weights).

## Decision

- `multitaper_line_removal(samples, sample_rate, half_bandwidth, *, probability=None,
  num_tapers=None, one_sided=None, nfft=None, adaptive=False)` returns
  `LineRemoval(spectrum, line_frequencies, line_amplitudes, residual)`. In C# the function is
  `Spectral.MultitaperLineRemoval`, with real and complex overloads, and returns
  `LineRemovalResult`.
- **Detection.** Run the harmonic F-test with the same tapers and `nfft`. A bin is a line when
  its `p < probability` (default `1/N`, Thomson's usual level) and its `F` is the largest within
  `r = ⌊NW·M/N⌋` bins either side, the half-bandwidth in bins. Several taper bins could catch one
  line; this keeps only the peak of each. The window is circular on the `M`-bin grid. For real
  input, a bin past `M/2` stands for its mirror, since `F` is symmetric there. A tie goes to the
  bin that comes first in the returned order.
- **Removal.** All lines are subtracted at once with the F-test's `μ`. For complex input that is
  `μ·e^{2πi b n/M}`. For real input, a line at `0 < b < M/2` takes its mirror with it:
  `2·Re(μ·e^{2πi b n/M})`. A line at DC, or at `b = M/2`, subtracts `Re μ` times the real
  exponential. The phase is computed as `2π·((b·n) mod M)/M`.
- `spectrum` is `multitaper_psd` of the residual with the same arguments. `line_frequencies`
  and `line_amplitudes` are the F-test's frequencies and `μ` at the detected bins, in the
  returned order. `residual` is the samples with the lines removed, real for real input.
- Errors are those of the F-test and the PSD, plus `probability` outside `(0, 1]`.

## Consequences

- Lines closer together than `2W` are not separated; this rule finds at most one of them. That
  is a limit of the F-test at that bandwidth.
- Lines are removed at bin frequencies. A line between bins leaves a remainder, and `nfft`
  padding shrinks it.
- Expected values come from the stdlib multitaper generator. It runs its own F-test, applies
  the detection rule, subtracts the lines and computes the PSD of the residual by direct sums.
  A by-hand case: a pure bin-centred complex tone has a zero F-test residual, so `F = ∞`, and
  removing it leaves a residual and spectrum of round-off.
