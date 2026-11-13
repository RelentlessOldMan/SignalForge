# 📶 SignalForge

Signal generation, DSP and measurement, built twice: once in Python, once in C#/.NET. The two
implementations share nothing at runtime. They share test vectors and conventions, and both must
produce the same numbers.

> Early days. The foundation is in: signals, units, tones, PRBS, power measurements, spectra (FFT,
> windows, Welch PSD, occupied bandwidth, channel power), QPSK mapping
> and bit errors, all checked against shared vectors in both languages. The first end-to-end slice
> (a QPSK link with EVM and BER) is next. See [docs/status.md](docs/status.md).

## Why

Most signal toolkits live in one language, and their results are only as trustworthy as the one
implementation. Writing everything twice, from the same written conventions, catches the mistakes
that one implementation hides: an off-by-one window, a power that should have been divided by N, a dB
that should have been 20·log10. When Python and C# agree on a value derived by hand, the value is
probably right.

## Usage

Python (3.10+, NumPy only):

```python
from signalforge import tone, power_stats, prbs, qpsk_map, qpsk_demap_hard, bit_errors

x = tone(sample_rate=1e6, num_samples=4096, frequency=125e3, amplitude=0.5)
print(power_stats(x).mean_power)          # 0.25

bits = prbs(9, 1022)
print(bit_errors(bits, qpsk_demap_hard(qpsk_map(bits))).errors)   # 0
```

C# (.NET 10, no package dependencies):

```csharp
using SignalForge;

var x = Waveforms.Tone(1e6, 4096, 125e3, amplitude: 0.5);
Console.WriteLine(Measurements.PowerStats(x).MeanPower);   // 0.25

var bits = Waveforms.Prbs(9, 1022);
Console.WriteLine(Metrics.BitErrors(bits, Modulation.QpskDemapHard(Modulation.QpskMap(bits))).Errors);
```

Neither package is published yet; build from source (commands below).

## How it works

- **Conventions first.** [docs/conventions.md](docs/conventions.md) pins down every definition that
  two implementations could disagree on: dB and dBFS, FFT scaling, QPSK Gray mapping, PRBS
  polynomials and bit order.
- **Shared vectors.** [vectors/cases](vectors/cases) holds JSON test cases with expected values from
  analytical or hand derivations, never from SignalForge's own output. Each language has a small
  runner that executes every case.
- **Strict licensing.** Only MIT, BSD-2, BSD-3, Apache-2.0 and ISC dependencies. Every one is
  recorded, with how its license was checked, in [docs/dependencies.md](docs/dependencies.md).
- Decisions are written up in [docs/adr](docs/adr); the overall shape is in
  [docs/architecture.md](docs/architecture.md).

## Layout

```
python/      the Python package (src/signalforge) and its tests
dotnet/      the C# library (src/SignalForge) and its tests
vectors/     shared test vectors, run by both
docs/        conventions, architecture, ADRs, dependencies, status
```

Build and test:

```
python -m venv .venv && .venv/Scripts/pip install -e python[dev]   # bin/ on Linux and macOS
cd python && pytest

cd dotnet && dotnet test
```

## Contributing

This is a personal tool, published as-is, and doesn't take issues or pull requests. Fork it and make it your own. 📶

## License

MIT — see [LICENSE](LICENSE). © 2026 RelentlessOldMan.
