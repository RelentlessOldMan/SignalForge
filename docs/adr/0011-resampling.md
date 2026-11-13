# 0011: Resampling by a rational factor

Date: 2026-11-13. Status: accepted.

## Context

Changing sample rate is the next building block: a receiver decimates after mixing, a generator
interpolates to a DAC rate, and comparing two captures often needs a common rate. The FIR designs
from ADR 0010 supply the anti-aliasing filter. Choices to fix now: one operation or several, how
the output lines up with the input in time, the gain, the output length, and the default filter.

## Decision

- **One primitive**, `resample(x, up, down, taps=None)`: zero-stuff by `up`, filter, keep every
  `down`-th sample. `interpolate(x, factor)` is `resample(x, factor, 1)` and `decimate(x, factor)`
  is `resample(x, 1, factor)`, so there is one definition to test. `up` and `down` are reduced by
  their greatest common divisor first, so `(4, 2)` and `(2, 1)` are the same operation.
- **Aligned, not causal.** Output sample `m` sits at input time `m·down/up`: the filter's delay of
  `(N − 1)/2` samples at the upsampled rate is removed, so the taps must have **odd** length. This
  is what measurement code wants (a tone keeps its phase, a symbol keeps its index) and what other
  tools' polyphase resamplers do. Streaming (causal, with state) is a later, separate class.
- **Gain**: the taps are designed with unit DC gain, and the filtered zero-stuffed signal is
  multiplied by `up`, so a constant keeps its level away from the edges, with a small ripple
  because each polyphase branch of the taps sums to only nearly `1/up` (about 0.1% with the
  default taps at 2/1).
- **Length** `⌈len(x)·up/down⌉`: every output whose time falls inside the input span.
- **Default taps** (`resample_taps(up, down)`): `fir_lowpass(20·max(up, down) + 1, 1/(2·max(up,
  down)), 1)`, Hamming window, the long-standing default of other polyphase resamplers, so results
  look like what users already know. A caller with a stricter spec passes their own taps.
- Implemented directly from the definition (C# skips the zero products; Python convolves the
  zero-stuffed signal), not with an FFT.

## Consequences

- Near the start and the end the filter runs into the zeros outside the input, so the first and
  last `(N − 1)/(2·up)` or so output samples are attenuated. Tests compare interior samples.
- The default filter's cutoff sits at the lower of the two Nyquist frequencies, where a Hamming
  design is at −6 dB, so the top of the band aliases a little. That is the usual trade for short
  filters; `taps` exists for anything stricter.
