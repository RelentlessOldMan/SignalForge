# ADR 0100: Writing multi-capture SigMF recordings

Status: accepted, 2026-11-15. Extends [ADR 0097](0097-sigmf-captures.md), which left writing out.

## Context

`read_sigmf_captures` (ADR 0097) splits a one-channel recording into one signal per capture. ADR 0097
left the writer for later. The open question was when the time origins of consecutive signals are
close enough to be one recording.

## Decision

- Python `write_sigmf_captures(path, segments, datatype=None)`. C#
  `SignalFiles.WriteSigmfCaptures<T>(path, segments, datatype = null)`. `datatype` defaults as for
  `write_sigmf`.
- The segments are a non-empty list of signals of one kind. Their samples are joined in order, and
  segment `j` starts at `start_j`, the sum of the lengths before it. Segment `j` gives the capture
  `{"core:sample_start": start_j, "core:frequency": its center frequency}`.
- The time origins must agree **exactly** with what the reader would compute. Each later segment's
  time origin must equal `t₀ + start_j / sample_rate` in binary64, where `t₀` is the first
  segment's. Anything else is rejected rather than rounded, so no segment's timing is lost
  silently. A reader's output always passes, because it is made by that same expression.
- Everything else must be identical, as for `write_sigmf_channels`: the sample rate, units,
  impedance and metadata other than `core:annotations`. They are compared as the `global` objects
  `write_sigmf` would write.
- Only the last segment may be empty, because the reader needs each start to be greater than the
  one before. A single empty segment is allowed.
- **Annotations**: each segment's list is checked as for `write_sigmf`. Its `core:sample_start`
  values are moved up by `start_j`, and the lists are joined in order. In every segment but the
  last, each annotation must start before the segment's end. Otherwise the reader would give it to
  a later segment. Spans are not checked, as in ADR 0061.
- The output has the same key order as `write_sigmf`. One segment gives exactly the `write_sigmf`
  files.
- Errors, all raised before either file is touched: an empty list or a non-signal, mixed kinds, an
  empty segment that is not last, a differing shared field, a time origin off the expression, and
  an annotation past its segment.

## Consequences

- Reading a recording with `read_sigmf_captures` and writing the segments back gives the same
  samples, frequencies, time origins and annotations. A recording that starts with an empty capture
  cannot be made.
- The expected values are files worked by hand in the tests, and round trips through the reader.
