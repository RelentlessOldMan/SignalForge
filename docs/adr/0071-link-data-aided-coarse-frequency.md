# ADR 0071: A data-aided coarse frequency with the link equalizer

Status: accepted, 2026-11-13

## Context

ADR 0070 takes the link's frequency from the preamble when the equalizer runs, but only as a
correction of at most `±R/(2B)` (±15.6 Hz at 1 kHz and `B = 32`) to the blind coarse estimate
`f₁` of step 2. Through an echo of 0.9 one symbol late, 8-PSK's 8th-power estimate is often far
outside that: at 12 dB it was 31.25 Hz off in two of four runs, as the 8th power of symbols that
heavy interference has blurred has almost no mean left, and the spectrum's peak is mostly
noise. Its range is also only `±R/16`.

## Decision

With `equalizer_taps` and `P ≥ 2`, step 2's `f₁` is data-aided instead of blind (with `P = 1`
the blind estimate stays). It comes from the phase
steps between neighbouring preamble symbols, at lag 1:

- `d[i] = r[i+1]·conj(r[i])` and `e[i] = a[i+1]·conj(a[i])` for the known preamble `a`;
- `D(k) = Σ_{i=0}^{P−2} conj(e[i])·d[k+i]` for `k = 0 … len(r) − N`;
- `k₁` the first `k` with the largest `|D(k)|`, and `f₁ = arg(D(k₁))·symbol_rate/(2π)`.

A frequency offset turns every `d[i]` by the same `2πf/R`, so `|D(k)|` does not depend on it
and the search over `k` finds the preamble at any offset. The known symbols take the
modulation's data out: through a channel `Σ_m h_m·a[i−m]`, `E[d[i]·conj(e[i])]` is `|h₀|²` (real)
plus terms in `E[a²]`, which is 0 for every constellation here. The interference only adds
noise. The range is `±R/2`.

Steps 3 to 7 then run as before on that `f₁`: the block frame search (ADR 0068) and the
preamble's least-squares line (ADR 0070), which corrects `f₁` by up to `±R/(2B)`. The frame start
`k₀` is still step 3's; `k₁` is used only for `f₁`.

- Lag 1, not longer: a lag of `L` cuts the noise about `L` times but cuts the range to
  `±R/(2L)`. At lag 1 the error was about 5 Hz on the echo below, a third of the correction's
  range.
- Only with the equalizer: without it the blind estimators are what the chain has always used,
  and they are fine where there is no strong interference.

## Consequences

- Equalizer runs report a different `frequency_offset_hz` (steps 2–6) and phase from before, and
  their noisy results change. The frame start is the same where the blind `f₁` was within the
  block search's reach.
- Measured on `1 + 0.9·z⁻¹` (delays 0 and 4 at 4 samples per symbol), 20000 symbols, a
  1000-symbol preamble, 11 taps and 2 feedback taps, four seeds, at offsets of 5, 37 and −120 Hz:
  8-PSK at 12 dB has a BER of 0.0001–0.001 and its frequency within 0.007 Hz (before, two of four
  runs at 5 and 37 Hz had a BER of 0.5, the estimate 31.25 Hz off). QPSK at 8 dB and 16-QAM at 14 dB keep their BERs (0.0002–0.0009 and
  under 0.0006) at 5 and 37 Hz; at −120 Hz, 12% of the symbol rate, 16-QAM rises to 0.002–0.004
  with its frequency still within 0.01 Hz.
- The deterministic preamble's interference leaves the lag-1 estimate a few hertz off, the same in
  every seed; the least-squares line removes it.
- The search costs one more pass of `P` products per start, as step 3 does.
