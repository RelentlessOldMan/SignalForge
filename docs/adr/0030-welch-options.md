# ADR 0030: Welch options: detrending and median averaging

Status: accepted, 2026-11-13

## Context

Welch's method averaged plain segments. Two common extensions change the result enough that both
languages must define them the same way: removing each segment's mean or trend before the window
(a DC offset or drift otherwise leaks through the window's sidelobes into the low bins), and
replacing the mean over segments by the median (a burst in one segment otherwise raises every bin
of the average). The median of exponentially distributed periodogram values sits below their mean,
so it needs a correction, and how that correction is defined for an even number of segments is a
choice.

## Decision

- **`detrend="none" | "constant" | "linear"`** on `welch_psd` and `spectrogram` (C#: the
  `Detrend` enum), applied to each raw segment before the window. The linear fit is the
  least-squares line over the segment's own sample indices, complex values fitted as complex.
  The default stays `"none"`, so existing results do not change.
- **`average="mean" | "median"`** on `welch_psd` only (C#: `WelchAverage`). The median is per bin;
  for an even count it is the mean of the two middle values, as NumPy's `median` does.
- **The median is divided by `b(K)`, the exact expected median of `K` unit-mean exponential
  values**, for odd and even `K` alike: `H_K − H_m` for `K = 2m+1` and `H_K − H_m + 1/K` for
  `K = 2m`. Some libraries use the odd-`K` series for even `K` too; we use the exact value for
  both, so results for an even number of segments differ from theirs.
- The correction is applied to the two-sided values; one-sided folding is a fixed scaling and
  commutes with it.

## Consequences

- The correction makes the median unbiased only for Gaussian noise in independent
  (non-overlapping) segments, in bins whose power is exponentially distributed. It is not right
  for DC and Nyquist bins of real input, for overlapping segments (correlated values), or for
  a steady tone (which then reads `1/b(K)` high). The conventions say so; callers who need a
  calibrated tone level use `average="mean"` or the tone measurements.
- Expected values come from a stdlib generator that detrends by solving the uncentred normal
  equations (a different formula from the conventions' centred one), sums the DFT term by term,
  and checks `b(K)` against a numerical integral of the order-statistic densities; plus hand
  cases.
