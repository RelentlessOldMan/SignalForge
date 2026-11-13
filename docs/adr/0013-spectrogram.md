# 0013: Spectrogram

Date: 2026-11-13. Status: accepted.

## Context

Welch's PSD (ADR 0006) averages a signal's segments. Watching a signal change over time (a hop, a
burst, a chirp) needs the segments kept. Choices to fix now: how the spectrogram relates to the
PSD, how a 2-D result looks in each language and in the vectors, and what time each row stands for.

## Decision

- **Same segments, same scaling as Welch.** `spectrogram(samples, sample_rate, nperseg, ...)`
  takes Welch's arguments and keeps each segment's PSD as a row, so the mean of the rows is
  `welch_psd`. One definition of segmenting, windowing, scaling and sidedness, shared in code by
  both functions in each language.
- **`nperseg` is required.** Welch defaults to the whole input, which for a spectrogram would give
  one row; there is no default that suits most signals.
- **Rows are segments.** Python returns a 2-D array of shape `(num_segments, num_bins)`; C# returns
  `double[][]`, one array per segment (jagged arrays map one to one onto JSON and onto the Python
  rows, where `double[,]` would need its own conversion). Vectors write the PSD as a list of rows;
  both runners compare 2-D results element by element.
- **Row times are segment centers**, `(s·step + nperseg/2)/fs` seconds from the first sample, the
  usual choice in other tools; the caller adds the signal's `time_origin`.
- No zero padding, detrending or per-frame scaling options yet, as for Welch.

## Consequences

- Vectors can't express argument errors one language's types already rule out (a float `nperseg`,
  a one-sided flag for complex samples in C#); Python unit tests cover those.
- Spectrogram options (zero padding, detrending, magnitude or dB output) are later work.
