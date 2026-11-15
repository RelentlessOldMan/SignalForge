# ADR 0094: WAV cue points

Status: accepted, 2026-11-14. Its (position, label) cue shape is replaced by (position, length,
label) in [ADR 0095](0095-wav-cue-regions.md), which also reads and writes `ltxt`.

## Context

Recorders and editors mark positions in a WAV file (a trigger, a burst start, a region boundary)
with a `cue ` chunk: a list of cue points, each with an ID and a sample position. Names for them
go in a `LIST` chunk of form type `adtl` (associated data), as `labl` subchunks keyed by cue ID.
SignalForge skips both, so the marks are lost on the way through ([ADR 0091](0091-wav-info.md)).
A cue point carries more fields than a plain file uses: a play-order position, and a chunk ID,
chunk start and block start for files whose audio is split across a `wavl` list of chunks.

## Decision

- **API**: Python `read_wav_cues(path) -> list[tuple[int, str]]`, C#
  `ReadWavCues(path) -> IReadOnlyList<(long Position, string Label)>`: one entry per cue point, in
  the `cue ` chunk's order, with its position in sample frames from the start of the data and its
  label (`""` when it has none). `write_wav` (both C# overloads) takes an optional `cues`, a
  sequence of (position, label) pairs. `read_wav` and `read_wav_info` are unchanged.
- **Cue IDs are not exposed.** They only link labels to points. The writer numbers the points 1,
  2, 3, … in order; the reader checks them and then drops them.
- **Writing**: with a non-empty `cues`, a `cue ` chunk goes after the `data` chunk and its pad
  byte: a 32-bit count, then 24 bytes per point: the ID, the position (play order), `data`,
  chunk start 0, block start 0, and the position again (sample offset). Then, if any label is
  non-empty, a `LIST` chunk of form type `adtl` with one `labl` subchunk per non-empty label in
  order: the cue ID, the text and one NUL, padded to even. Then the `LIST`/`INFO` chunk, if
  any. A position is a whole number from 0 to the number of samples per channel (the end is
  allowed). A label is printable ASCII (`0x20`–`0x7E`). With no cues, or an empty sequence, the
  file is byte-for-byte what it was before.
- **Reading**: the RIFF walk is the one `read_wav_info` uses. The file needs a `fmt ` chunk of at
  least 16 bytes with a non-zero block align, and a `data` chunk. The number of frames is the data
  size divided by the block align, rounded down. There may be at most one `cue ` chunk. Its size
  must be exactly 4 + 24 × the count. For each point:
  - the chunk ID must be `data`, and chunk start and block start must be 0 (no `wavl` lists);
  - the sample offset is the position, and must be at most the number of frames;
  - the play-order field is not checked, since some writers leave it 0;
  - an ID used twice is rejected.

  Every `LIST` chunk of form type `adtl` is read; its `labl` subchunks need at least 4 bytes, and
  their text is the body after the ID up to the first NUL, read as Latin-1, as `INFO` texts are.
  Other `adtl` subchunks (`note`, `ltxt`) are skipped. A label whose ID has no cue point, or a
  second label for the same ID, is rejected. A file with no `cue ` chunk has no cues.
- **Expected values**: the WAV generator packs the `cue ` and `adtl` chunks with `struct` from the
  layout above; Python's `wave` module checks that the audio of those PCM files still reads.

## Consequences

- Region lengths (`ltxt`), notes, `smpl` loops and `wavl` lists are still not read.
- Cue IDs from another writer are not kept: a file read and written back has its points renumbered
  1, 2, 3, …
