# Architecture

SignalForge is one library written twice: a Python package and a .NET library. Neither calls the
other. They agree because both follow [conventions.md](conventions.md) and both pass the same
language-neutral test vectors in [`vectors/`](../vectors/).

## Repository

```
python/                 Python package `signalforge` (src layout, flit_core, NumPy)
  src/signalforge/
  tests/
dotnet/                 .NET library `SignalForge` (net10.0, base class library only)
  src/SignalForge/
  tests/SignalForge.Tests/
vectors/                shared test vectors: JSON cases, later binary sample files
docs/                   conventions, architecture, dependencies, testing, decisions, status
.github/workflows/      CI: both languages build, lint and run the shared vectors
```

## Modules

Modules are namespaces (C#) and submodules (Python) inside **one** package per language for now. A
module moves into its own project/package only when it brings a dependency the rest should not carry
(hardware drivers, a plotting library) or grows big enough that separate versioning pays off. See
[ADR 0002](adr/0002-one-package-per-language.md).

| Module | Python | C# | Holds | State |
|---|---|---|---|---|
| Core | `signalforge.core` | `SignalForge` | `Signal` (samples + sample rate, center frequency, time origin, units, impedance, metadata) | built |
| Units | `signalforge.units` | `SignalForge.Units` | dB, dBm, voltage/power conversions | built |
| Waveforms | `signalforge.waveforms` | `SignalForge.Waveforms` | tones, PRBS; later multitone, chirp, pulse, noise | started |
| Measurements | `signalforge.measurements` | `SignalForge.Measurements` | power statistics (mean, RMS, peak, PAPR, DC); later spectral and RF measurements | started |
| Modulation | `signalforge.modulation` | `SignalForge.Modulation` | QPSK map and hard demap; later PSK/QAM, pulse shaping, demodulators | started |
| Metrics | `signalforge.metrics` | `SignalForge.Metrics` | bit error counts, EVM, QPSK BER theory ([ADR 0007](adr/0007-pulse-shaping-channel-evm.md)) | started |
| Conformance | `signalforge.conformance` | test project | loads and runs `vectors/` cases | built |
| Spectral | `signalforge.spectral` | `SignalForge.Spectral` | FFT (C#: own radix-2 + Bluestein), frequency axes, windows, Welch PSD, spectrogram ([ADR 0013](adr/0013-spectrogram.md)), occupied bandwidth, channel power ([ADR 0006](adr/0006-fft-windows-spectra.md)) | started |
| DSP | `signalforge.dsp` | `SignalForge.Dsp` | convolution, upsampling, RRC taps and pulse shaping ([ADR 0007](adr/0007-pulse-shaping-channel-evm.md)); windowed-sinc FIR design, Kaiser parameters, frequency response and the streaming `FirFilter` ([ADR 0010](adr/0010-fir-design-streaming.md)); rational resampling, interpolation and decimation ([ADR 0011](adr/0011-resampling.md)); later IIR design, streaming resampling, mixing | started |
| Channel | `signalforge.channel` | `SignalForge.Channel` | AWGN at Es/N0, frequency offset; later phase noise, multipath | started |
| Sync | `signalforge.sync` | `SignalForge.Sync` | block timing, QPSK frequency, phase and block-phase estimates ([ADR 0008](adr/0008-block-synchronization.md)); later tracking loops | started |
| Link | `signalforge.link` | `SignalForge.Link` | end-to-end QPSK link run and its JSON report ([ADR 0009](adr/0009-qpsk-link-report.md)) | started |
| Files | `signalforge.files` | `SignalForge.SignalFiles` | raw sample encoding, SigMF-layout recordings ([ADR 0012](adr/0012-signal-files.md)); later WAV, NumPy, streaming | started |
| Standards | | | one subpackage per standard, versioned, never mixed into generic code | planned |
| Hardware | | | separate package, never a dependency of the core | planned |

Demodulation sits with modulation until it grows. Synchronization has its own module (`sync`), and
end-to-end runs that string the modules together live in `link`.

## Signals

- Low-level functions take and return plain arrays (`numpy.ndarray`, `ReadOnlySpan<T>` / `T[]`). No
  metadata, no allocation beyond the output.
- `Signal` wraps samples with their metadata for high-level use. It is immutable: operations return
  a new `Signal`. In C# it is `Signal<T>` over `double` or `Complex` (later `float` and
  `Complex32`-style types).
- Streaming will be a separate interface over chunks of samples, added with the first operation that
  needs state across chunks (a filter). Finite-buffer functions stay as they are.

## Measurement results

Measurements that produce more than one meaningful number return a small immutable result record
(`PowerStats`), with plain numeric fields in the documented units. Results are serializable to JSON
with the same field names in both languages (Python `snake_case`; C# `PascalCase` properties mapped
to `snake_case` in JSON). Limit checking and reports build on these records later.

## Naming across languages

The same operation has the same name modulo language style: `lin_to_db` / `LinToDb`,
`power_stats` / `PowerStats`. The conformance vectors use the Python spelling as the operation id.
