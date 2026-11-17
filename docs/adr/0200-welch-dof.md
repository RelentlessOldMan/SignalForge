# ADR 0200: Welch equivalent degrees of freedom

Status: accepted, 2026-11-16. It goes with the coherence threshold (ADR 0199).

## Context

- **Independent segments.** A Welch average of `K` independent segments has `2K` degrees of
  freedom per bin.
- **Overlapped segments.** These are correlated, so they are worth less. Welch (1967) gives the
  equivalent count from the window's overlap correlation.
- **What it is for.** Callers need it to set confidence intervals and to choose the effective
  `K` for `coherence_threshold`.

## Decision

- **The API.**
  - Python: `welch_dof(nperseg, noverlap, num_segments, *, window="hann", beta=None)` in
    `spectral`.
  - C#: `Spectral.WelchDof(int nperseg, int noverlap, int numSegments, WindowType window =
    WindowType.Hann, double? beta = null)`.
  - Both return a float.
- **The definition.**
  - `ν = 2K / (1 + 2 Σ_{l=1}^{K−1} (1 − l/K)·ρ(l)²)`.
  - `ρ(l) = Σ_n w[n]·w[n + l·S] / Σ_n w[n]²` is the window's overlap correlation at `l` steps,
    with step `S = nperseg − noverlap`.
  - `ρ(l)` is 0 once `l·S ≥ nperseg`.
  - The window is the one `welch_psd` uses: periodic, from the window table.
- **The rules.**
  - `nperseg ≥ 1`, `0 ≤ noverlap < nperseg` and `num_segments ≥ 1`, all integers.
  - The window must not be all zeros.
  - Anything else is `invalid_argument`.
  - `K = 1` gives 2.
- **Gaussian data.** The formula assumes Gaussian data, with a spectrum that is smooth across
  the window's bandwidth. It is an approximation, as in Welch's paper.

## Consequences

- **Vectors.** They are hand cases:
  - rectangular with no overlap gives `2K`;
  - rectangular at 50 % (`ρ(1) = 1/2`) gives 4.5 for `K = 3`;
  - rectangular at 75 % gives `64/17` for `K = 4`;
  - Hann `N = 4` at 50 % (`w = [0, ½, 1, ½]`, `ρ(1) = 1/6`) gives `81/14` for `K = 3`;
  - `K = 1` gives 2.

  They also cover the argument errors.
- **Using it with the threshold.** `welch_dof(...)/2` is the effective `K` for
  `coherence_threshold`. That threshold needs an integer `K`, so the caller rounds down.
