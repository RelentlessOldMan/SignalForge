# ADR 0101: Bootstrap maxima for a Lomb-Scargle search

Status: accepted, 2026-11-15. Complements [ADR 0098](0098-lomb-scargle-baluev.md).

## Context

The Baluev estimate (ADR 0098) is an approximation for white Gaussian noise. A bootstrap makes no
such assumption. It resamples the data's own values at the same times, so any periodicity is lost
while the spread of the values is kept. It then records the highest peak of each draw's
periodogram over the search grid. The fraction of draws whose peak exceeds the observed one
estimates the false-alarm probability. The sorted peaks give a level for any chosen probability.

## Decision

- Python `lomb_scargle_bootstrap(times, values, frequencies, draws, *, seed, center=True)`. C#
  `Spectral.LombScargleBootstrap(times, values, frequencies, draws, seed, center = true)`, where
  `seed` is an `int` or a `Random`. Python takes an integer or a `numpy.random.Generator`, as for
  `awgn`. The result is `draws` maxima in draw order, not sorted, so a caller can see how the
  estimate settles.
- Each draw picks `N` indices uniformly from `0 … N − 1` with replacement: Python
  `rng.integers(0, N, size=N)`, C# `rng.Next(N)` `N` times. Its values are the original values at
  those indices, at the original times. Its peak is the largest `lomb_scargle(times, drawn,
  frequencies, center=center)` value, in the standard normalization.
- A draw that the standard normalization cannot scale gives a peak of 0. That is a draw whose
  values are all equal when centered, or all zero when not. Such a draw has no power to exceed
  anything.
- Errors: those of `lomb_scargle` on the original values, so values the normalization cannot scale
  are rejected; `frequencies` empty; and `draws` below 1. The arguments are checked before any
  random numbers are drawn.

## Consequences

- The random streams differ between the languages (conventions: Random), so only seed-independent
  results are compared exactly. One such result is a constant, uncentered series, where every draw
  is the original. Its peak comes from the generator's own least-squares fit. The other checks
  are statistics: on Gaussian noise, the peaks are compared with the Baluev estimate, and a strong
  sinusoid's peak is above every draw.
- Each draw costs a full periodogram, so the cost is `draws·N·len(frequencies)`.
