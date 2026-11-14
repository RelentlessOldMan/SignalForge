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
| Waveforms | `signalforge.waveforms` | `SignalForge.Waveforms` | tones, multitone (Newman phases), linear chirp, pulse train, PRBS | built |
| Measurements | `signalforge.measurements` | `SignalForge.Measurements` | power statistics (mean, RMS, peak, PAPR, DC); tone metrics (SNR, SINAD, THD, ENOB); SFDR and spurs; later RF measurements | started |
| Modulation | `signalforge.modulation` | `SignalForge.Modulation` | QPSK, 8-PSK, 16-QAM and 64-QAM ([ADR 0052](adr/0052-qam64.md)) map, hard demap ([ADR 0035](adr/0035-psk8-qam16.md)) and max-log soft demap ([ADR 0039](adr/0039-soft-demapping.md)); continuous-phase M-FSK and its noncoherent detector ([ADR 0054](adr/0054-fsk.md)); later other constellations, pulse shaping, demodulators | started |
| Metrics | `signalforge.metrics` | `SignalForge.Metrics` | bit error counts, EVM, QPSK BER theory ([ADR 0007](adr/0007-pulse-shaping-channel-evm.md)), 16-QAM and 8-PSK BER and SER theory ([ADR 0037](adr/0037-error-rate-theory.md)), noncoherent M-FSK ([ADR 0054](adr/0054-fsk.md)) | started |
| Conformance | `signalforge.conformance` | test project | loads and runs `vectors/` cases | built |
| Spectral | `signalforge.spectral` | `SignalForge.Spectral` | FFT (C#: own radix-2 + Bluestein), frequency axes, windows, Welch PSD with detrending, median averaging ([ADR 0030](adr/0030-welch-options.md)) and zero padding ([ADR 0031](adr/0031-zero-padding.md)), spectrogram ([ADR 0013](adr/0013-spectrogram.md)), occupied bandwidth, channel power ([ADR 0006](adr/0006-fft-windows-spectra.md)), ACPR ([ADR 0019](adr/0019-acpr.md)) | started |
| DSP | `signalforge.dsp` | `SignalForge.Dsp` | convolution, upsampling, RRC taps and pulse shaping ([ADR 0007](adr/0007-pulse-shaping-channel-evm.md)); windowed-sinc FIR design, Kaiser parameters, least-squares FIR design ([ADR 0029](adr/0029-least-squares-fir.md)), equiripple FIR design, including Hilbert transformers and differentiators ([ADR 0024](adr/0024-equiripple-fir.md), [ADR 0026](adr/0026-antisymmetric-equiripple.md)), frequency response, group delay ([ADR 0028](adr/0028-group-delay.md)) and the streaming `FirFilter` ([ADR 0010](adr/0010-fir-design-streaming.md)); Butterworth IIR design (low-pass, high-pass, band-pass, band-stop; [ADR 0016](adr/0016-band-butterworth.md)) and Chebyshev types I and II (low-pass, high-pass, band-pass, band-stop; [ADR 0018](adr/0018-chebyshev-type-1.md), [ADR 0020](adr/0020-chebyshev-type-2.md), [ADR 0021](adr/0021-band-chebyshev.md)) and elliptic (low-pass, high-pass, band-pass, band-stop; [ADR 0022](adr/0022-elliptic.md), [ADR 0023](adr/0023-band-elliptic.md)) and Bessel (low-pass, high-pass, band-pass, band-stop; [ADR 0025](adr/0025-bessel.md), [ADR 0032](adr/0032-band-bessel.md)) and first- and second-order all-pass sections ([ADR 0033](adr/0033-allpass.md)) as second-order sections, their response and group delay, zero-phase filtering ([ADR 0017](adr/0017-zero-phase-filtering.md)) and the streaming `IirFilter` ([ADR 0014](adr/0014-iir-filters.md)); rational resampling, interpolation and decimation ([ADR 0011](adr/0011-resampling.md)) and the streaming `Resampler` ([ADR 0027](adr/0027-streaming-resampling.md)); later more IIR designs | started |
| Channel | `signalforge.channel` | `SignalForge.Channel` | AWGN at Es/N0, frequency offset, IQ imbalance, DC offset ([ADR 0034](adr/0034-iq-impairments.md)), Wiener phase noise ([ADR 0036](adr/0036-phase-noise.md)), static multipath ([ADR 0038](adr/0038-multipath.md)), fractional delay ([ADR 0040](adr/0040-fractional-delay.md)), Rician block fading ([ADR 0041](adr/0041-block-fading.md)), sample clock offset ([ADR 0045](adr/0045-clock-offset.md); in the link, [ADR 0046](adr/0046-link-tracking-loops.md); link phase noise, [ADR 0047](adr/0047-link-phase-noise.md); 16-QAM in the link, [ADR 0050](adr/0050-link-modulation.md); 8-PSK, [ADR 0051](adr/0051-psk8-link.md); 64-QAM, [ADR 0053](adr/0053-qam64-link.md)); later continuous fading | started |
| Sync | `signalforge.sync` | `SignalForge.Sync` | block timing, QPSK frequency, phase and block-phase estimates ([ADR 0008](adr/0008-block-synchronization.md)), Gardner timing recovery ([ADR 0043](adr/0043-gardner-timing.md)), QPSK carrier tracking ([ADR 0044](adr/0044-qpsk-carrier-loop.md)), 8-PSK and 16-QAM carrier tracking ([ADR 0048](adr/0048-psk8-qam16-carrier-loops.md)), power-spectrum frequency offset ([ADR 0049](adr/0049-power-frequency-offset.md)), 8-PSK phase and block phases ([ADR 0051](adr/0051-psk8-link.md)) | started |
| Link | `signalforge.link` | `SignalForge.Link` | end-to-end QPSK link run and its JSON report ([ADR 0009](adr/0009-qpsk-link-report.md)); 16-QAM, 8-PSK and 64-QAM ([ADR 0050](adr/0050-link-modulation.md)), 2- and 4-FSK with noncoherent detection ([ADR 0057](adr/0057-fsk-link.md)) | started |
| Files | `signalforge.files` | `SignalForge.SignalFiles` | raw sample encoding, SigMF-layout recordings ([ADR 0012](adr/0012-signal-files.md)), WAV ([ADR 0055](adr/0055-wav.md)), NumPy `.npy` ([ADR 0056](adr/0056-npy.md)); later streaming | started |
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
