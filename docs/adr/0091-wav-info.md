# ADR 0091: WAV `LIST`/`INFO` text tags

Status: accepted, 2026-11-14

## Context

WAV files ([ADR 0055](0055-wav.md)) often carry text tags in a `LIST` chunk of form type `INFO`:
`INAM` (title), `IART` (artist), `ICMT` (comment), `ICRD` (date), `ISFT` (software) and others,
each a four-character ID and a NUL-terminated string. SignalForge writes only the audio and skips
every other chunk on read, so a recording's description is lost on the way through. Tags are the
one piece of WAV metadata that recorders, editors and `ffmpeg` all write.

## Decision

- **API**: Python `write_wav(path, channels, sample_format="f32", info=None)` and
  `read_wav_info(path) -> dict[str, str]`; C# `WriteWav(path, channels, sampleFormat, info)` with
  `info` an optional `IEnumerable<KeyValuePair<string, string>>?`, and
  `ReadWavInfo(path) -> OrderedDictionary<string, string>`. `read_wav` is unchanged and still
  ignores the tags; reading them is a separate call, so code that reads audio never fails on a tag.
- **Writing**: with a non-empty `info`, a `LIST` chunk of form type `INFO` goes after the `data`
  chunk and its pad byte, holding one subchunk per tag in the mapping's order: the ID, a 32-bit
  size, the text and one NUL, then a zero pad byte when that size is odd. An ID is four characters,
  each `A`–`Z` or `0`–`9`, used once. The text is printable ASCII (`0x20`–`0x7E`), possibly empty.
  With no `info`, or an empty one, the file is byte-for-byte what it was before.
- **Reading**: `read_wav_info` walks every chunk from byte 12 to the end, past `data`, and reads
  each `LIST` chunk whose first four body bytes are `INFO`, in file order; other `LIST` types
  (`adtl`, …) and other chunks are skipped. It needs `RIFF` and `WAVE`, not `fmt ` or `data`.
  Inside, subchunks are an ID, a size and a body padded to even, and must fit in the `LIST` body.
  The text is the body up to its first NUL, or the whole body without one. Each byte becomes the
  character with the same code (Latin-1), so reading never fails on text: UTF-8 or Windows-1252
  tags come back as their bytes, and the caller can re-decode them
  (`s.encode("latin-1").decode("utf-8")`). IDs are read the same way and not otherwise checked.
- **Rejected on read**: a chunk or subchunk that runs past its container, and an ID that appears
  twice, in the same `LIST` or in two of them. A walk, of the file or of a `LIST` body, ends when
  fewer than 8 bytes are left, which are ignored; so the pad byte of the last chunk may be missing,
  as many writers leave it out.
- **No parsing of values**: `ICRD` and the rest are returned as text; dates are not interpreted.
- **Expected values**: the WAV generator packs the chunks with `struct`, with the texts as literal
  bytes. Python's `wave` module, which skips chunks it does not know, checks that the audio of a
  tagged PCM file still reads.

## Consequences

- Other metadata chunks (`bext`, `cue `, `smpl`, `id3 `) are still skipped, on read and lost on a
  round trip.
- A caller who wants UTF-8 tags written has to choose ASCII text for now; writing other encodings
  can come later without changing what is read.
