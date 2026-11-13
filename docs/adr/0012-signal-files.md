# 0012: Signal files in the SigMF layout

Date: 2026-11-13. Status: accepted.

## Context

The two implementations so far meet only through JSON vectors and reports. Noisy signals can't be
compared sample by sample across languages (the random streams differ), so `docs/testing.md`
plans to exchange the samples themselves as files. Users need the same thing for captures from
instruments and other tools. Choices to fix now: which format, which sample types, how integers
scale, and where `Signal`'s own fields go.

## Decision

- **SigMF's layout**: a JSON `.sigmf-meta` beside a raw `.sigmf-data`. It is the open format other
  RF tools already read and write, raw data stays memory-mappable, and the metadata is plain JSON
  that both languages parse with their standard libraries (`json`, `System.Text.Json`), so there is
  no new dependency. The reference library is LGPL and the specification text is CC-BY-SA, so
  neither is used: the reader and writer are written from what the files look like.
- **Sample types**: complex and real; `f64`, `f32`, `i32`, `i16`, `i8`; both byte orders. Unsigned
  and half-float types are rejected until something needs them.
- **Integers scale to full scale 1.0** (`code / 2^(b−1)`), the usual meaning of an ADC capture, and
  writing refuses a value it would have to clip rather than clipping it silently.
- **Reading returns double precision** whatever the stored type, as everything else computes in
  double (conventions: Samples and numeric types).
- **`Signal`'s fields**: `sample_rate` and `center_frequency` map to SigMF's own fields; the time
  origin, units, impedance and plain metadata go in a `signalforge` extension namespace;
  namespaced metadata keys (`core:author`, `core:description`) are written as SigMF fields, so a
  round trip keeps everything.
- **One channel, one frequency.** Multi-channel files, header bytes inside the data, and captures
  at different frequencies are rejected rather than half-read.
- **Low-level `encode_samples` / `decode_samples`** are public too: they are the raw-file reader
  and writer, and the shared vectors test them byte for byte.
- In C#, the sample kind is a type argument (`ReadSigmf<Complex>`); a file of the other kind is an
  error, not a conversion.

## Consequences

- Each build writes files in both languages and both read all of them; the readings must agree
  (`docs/testing.md`, Cross-language checks).
- Streaming reads and writes, annotations, unsigned types, WAV and NumPy files are later work.
