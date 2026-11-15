# ADR 0095: WAV cue regions

Status: accepted, 2026-11-14. Changes the cue shape of [ADR 0094](0094-wav-cues.md).

## Context

A cue point marks one position. Editors mark a stretch of samples (a burst, a word, a loop) with a
cue point plus an `ltxt` subchunk in the `LIST`/`adtl` chunk: the cue ID, a length in sample frames,
a four-character purpose (`rgn ` for a region), country, language, dialect and code page fields,
and optional text. ADR 0094 skips `ltxt`, so a region comes back as its start only.

## Decision

- **A cue is (position, length, label)** in both directions, replacing ADR 0094's (position,
  label): Python `read_wav_cues(path) -> list[tuple[int, int, str]]` and
  `write_wav(..., cues: Sequence[tuple[int, int, str]])`; C# `(long Position, long Length, string
  Label)` in `ReadWavCues` and `WriteWav`. Length 0 is a plain point. One shape for both, rather
  than a second function or mixed pairs and triples, keeps the two languages' overloads equal. No
  release has shipped ADR 0094's shape, so nothing outside the repo breaks.
- **Writing**: a length is a whole number with position + length at most the number of frames.
  In the `LIST`/`adtl` chunk, written when any cue has a label or a length, each cue in order
  gets its `labl` (if the label is non-empty) and then, if its length is non-zero, an `ltxt` of
  20 bytes: the cue ID, the length, `rgn `, and country, language, dialect and code page each a
  16-bit 0; no text.
- **Reading**: an `ltxt` needs at least 20 bytes; its cue ID must name a cue point and may have
  only one `ltxt`; position + length must be at most the number of frames. The purpose, the four
  locale fields and any text are not checked and not returned. An `ltxt` of length 0 is the same
  as none. A cue without an `ltxt` has length 0.
- **Expected values**: the WAV generator packs `ltxt` subchunks with `struct` from the layout
  above, as for ADR 0094.

## Consequences

- Region text and purpose are not kept; a region read and written back is purpose `rgn `.
- Code written against ADR 0094's pairs must add the length.
