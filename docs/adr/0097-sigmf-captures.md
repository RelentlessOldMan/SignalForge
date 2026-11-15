# ADR 0097: Reading multi-capture SigMF recordings

Status: accepted, 2026-11-14. Extends [ADR 0012](0012-signal-files.md) and
[ADR 0061](0061-sigmf-annotations.md).

## Context

A SigMF recording's `captures` array splits the samples into segments: each capture starts at its
`core:sample_start` and runs to the next capture's start, and may give its own `core:frequency`. A
receiver that hops or retunes mid-recording writes one capture per tuning. `read_sigmf` returns one
`Signal` with one center frequency, so it rejects captures at different frequencies, and these
recordings could not be read.

## Decision

- **A new reader, `read_sigmf` unchanged**: Python `read_sigmf_captures(path) -> list[Signal]`,
  C# `ReadSigmfCaptures<T>(path)` returning `IReadOnlyList<Signal<T>>`, one signal per capture, in
  file order. `read_sigmf` still rejects differing frequencies (its message now names the new
  reader). One channel only: a recording with `core:num_channels` other than 1 is rejected, as
  channels and captures together would need a list of lists that nothing yet asks for.
- **Segments**: every capture needs `core:sample_start`, a JSON integer ≥ 0 (not a bool, not
  `2.0`). The first must be 0 and each must be greater than the one before (SigMF has them in
  order; a repeated start would be an empty segment with no meaning), and none may be past the
  last sample (a start equal to the number of samples is an empty last segment). Capture `j`
  holds samples `start_j` up to `start_{j+1}`, the last up to the end. No captures is one
  segment, all the samples, at frequency 0. `core:header_bytes` must still be the integer 0.
- **Per segment**: the center frequency is the capture's `core:frequency` (missing is 0); the time
  origin is the recording's time origin plus `start_j / sample_rate`, computed as that one
  addition of a division in binary64, so both languages agree to the bit. A capture's
  `core:datetime` and other fields are not read, as in `read_sigmf`. Rate, units, impedance and
  metadata other than annotations are the recording's, each segment its own copy.
- **Annotations** go to the last segment whose start is at most the annotation's
  `core:sample_start`, which is rebased to count from that segment's start (so it indexes that
  signal's samples); every other field, `core:sample_count` included, is kept as it is, and an
  annotation running past its segment is not cut or checked, as ADR 0061 leaves spans unchecked.
  A segment with no annotations has no `core:annotations` key.
- **Writing is not part of this decision.** A writer would have to decide when consecutive
  signals' time origins are close enough to be one recording; it waits until someone needs it.
- **Expected values**: the files generator packs the samples with `struct` and writes the metadata
  by hand; segment time origins are chosen exact in binary64 (for example 0.5 + 3/4). Implemented
  from the SigMF description, not its text.

## Consequences

- A segment's time origin is derived, not read from `core:datetime`, so absolute times are lost.
- A round trip through `write_sigmf` of one segment gives a one-capture recording with that
  segment's frequency and time origin.
