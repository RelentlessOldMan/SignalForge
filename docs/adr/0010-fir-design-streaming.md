# 0010: FIR design and the first streaming filter

Date: 2026-11-13. Status: accepted.

## Context

Resampling, channel selection and any receiver front end need low-pass, high-pass and band-pass
FIR filters, and real use filters a stream in chunks, which no SignalForge operation has done so
far: every function took a whole buffer. The architecture says streaming arrives with the first
operation that needs state across chunks. Choices to fix now: the design method, how taps are
scaled, the filter object's shape, and which samples it accepts.

## Decision

- **Windowed sinc**, the textbook method, with the windows we already have (symmetric form) and
  Hamming as the default. Equiripple (Parks–McClellan) design can come later as its own function.
  Each design is scaled to exactly unit gain at a reference frequency: DC for a low-pass, `fs/2` for
  a high-pass, the band center for a band-pass. These are the usual references, so the gains are
  what a user of other tools expects. A high-pass needs an odd number of taps.
- Filter length from a specification comes from **Kaiser's formulas** (`kaiser_parameters`), cited
  in the conventions, so a user can ask for an attenuation and a transition width.
- The functions live in `dsp` with the other tap generators (`rrc_taps`); names `fir_lowpass`,
  `fir_highpass`, `fir_bandpass`, `kaiser_parameters`, `fir_response`.
- **Streaming**: a small class, `FirFilter` in both languages, with `process(chunk)` returning one
  output per input and `reset()`. Direct form; the state is the last `N − 1` inputs. No overlap-add
  or FFT filtering yet: the tap counts in sight are small, and direct form is exact and easy to give
  expected values to. The streaming interface for whole pipelines is still to come; this class is
  its first building block.
- **Taps are real.** Every design so far is real, and a real filter on complex samples covers
  baseband. The filter's kind, real or complex samples, is fixed by its first non-empty chunk and
  cannot change until a reset, because the stored state would be the wrong kind.

## Consequences

- Splitting a signal into chunks never changes the output: any split concatenates to the first
  `len(x)` samples of the full convolution. The vectors test exactly that, with uneven splits.
- Windowed designs do not meet a ripple specification exactly: Kaiser's formulas are estimates,
  so a caller with a hard limit checks the response (`fir_response`).
- Complex taps (a shifted band-pass, a Hilbert transformer) would need a second taps kind later.
