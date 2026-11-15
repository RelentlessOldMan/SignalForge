# ADR 0096: Multi-channel SigMF recordings

Status: accepted, 2026-11-14. Extends [ADR 0012](0012-signal-files.md).

## Context

A SigMF recording may hold several channels: the global field `core:num_channels` gives their
number, and the data file interleaves them sample by sample (sample 0 of every channel, then
sample 1, and so on). Receivers with several antennas or a stereo audio capture write recordings
this way. `read_sigmf` rejects any `core:num_channels` other than 1, and a `Signal` is one channel,
so these recordings could not be read at all.

## Decision

- **New functions, the single-channel ones unchanged**: Python
  `read_sigmf_channels(path) -> list[Signal]` and
  `write_sigmf_channels(path, channels, datatype=None)`; C# `ReadSigmfChannels<T>(path)`
  returning `IReadOnlyList<Signal<T>>` and `WriteSigmfChannels<T>(path, channels, datatype)`.
  `read_sigmf` still rejects a recording of more than one channel, so a caller who expects one
  signal never gets the first channel of several without noticing. A list of one channel reads
  and writes the same files as the single-channel functions.
- **Channel count**: `core:num_channels` is a JSON integer from 1 to 65535 (`MAX_CHANNELS` /
  `SignalFiles.MaxChannels`; a bool or `2.0` is not an integer); missing means 1. The limit keeps
  a hostile file from asking for billions of empty signals, and is the WAV limit too.
- **Samples**: sample `k` of channel `c` is sample `k·N + c` of the data (`N` channels). The data
  must hold a whole number of frames of `N` samples, or the recording is rejected.
- **Everything else is shared**: every channel gets the recording's sample rate, center frequency,
  time origin, units, impedance and metadata, annotations included, read exactly as `read_sigmf`
  reads them; each channel's metadata is its own copy. An annotation's sample indices count
  samples of one channel, as the SigMF description has them.
- **Writing**: `channels` is a non-empty list of at most 65535 signals of one kind (real or
  complex) and one length. The metadata file is the one `write_sigmf` would write for each
  channel, with `core:num_channels` after `core:sample_rate` when there is more than one channel;
  every channel must give the same metadata file, so the sample rate, center frequency, time
  origin, units, impedance and metadata must agree exactly (`1` and `1.0` differ, since they are
  written differently). Anything else is rejected rather than taken from channel 0, so nothing a
  caller set is silently dropped.
- **Expected values**: the files generator packs the interleaved samples with `struct` and writes
  the metadata by hand, as for single-channel recordings; implemented from the SigMF description,
  not its text.

## Consequences

- Per-channel metadata (a different frequency or gain per channel), SigMF collections and
  non-interleaved layouts are not supported.
- Writing checks every channel's metadata by building it, so a write costs one metadata build per
  channel; metadata is small, so this does not matter.
