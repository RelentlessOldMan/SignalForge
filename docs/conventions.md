# Numerical conventions

Every SignalForge function in both languages follows these definitions. If code and this file
disagree, one of them is a bug; fix it and say which in `docs/status.md`. A new convention goes here
before the code that depends on it.

Status markers: **(implemented)** means code and tests use it today; **(defined)** means it is the
rule for code not written yet.

## Samples and numeric types

- Complex samples are `complex128` (Python) / `System.Numerics.Complex` (C#) by default. Real samples
  are `float64` / `double`. **(implemented)**
- Single precision (`complex64`, `float32`) is a storage and throughput format. Measurements
  accumulate in double precision whatever the input type. **(defined)**
- Low-level functions take plain arrays (NumPy arrays / `ReadOnlySpan<T>`). The `Signal` type carries
  metadata around them; nothing low-level requires it. **(implemented)**

## Arguments

- Sample rates and impedances must be positive and **finite**; NaN and infinity are rejected.
  **(implemented)**
- Counts (`n`, `num_samples`, `num_bits`, `order`, `seed`, `nperseg`, `noverlap`) are integers ≥ 0.
  Python accepts anything with `__index__` (so NumPy integers) and rejects floats, even whole ones
  like `3.0`; C# takes `int`. **(implemented)**
- Measurements reject non-finite input where a NaN would otherwise pass through silently
  (`power_stats` samples, PSD frequencies and values). **(implemented)**
- A bad argument raises `ValueError` (Python) or `ArgumentException` or a subclass (C#).
  **(implemented)**

## Complex baseband

- A complex baseband signal is `x[n] = I[n] + j·Q[n]`. I is the real part, Q the imaginary part.
  **(implemented)**
- The matching real passband signal is `s(t) = Re{ x(t) · e^{+j2π·fc·t} }
  = I(t)·cos(2π·fc·t) − Q(t)·sin(2π·fc·t)`, where `fc` is the signal's `center_frequency`.
  **(defined)**
- A positive frequency offset `Δf` multiplies by `e^{+j2π·Δf·t}` and moves energy to a *higher*
  frequency. **(defined)**
- Time of sample `n` is `t[n] = time_origin + n / sample_rate`. **(implemented)**

## Tones

- `tone(...)` with `complex=True` returns `A·e^{j(2π·f·t[n] + φ)}`; with `complex=False` it returns
  `A·cos(2π·f·t[n] + φ)`. `A` is the **peak** amplitude, `φ` is in radians. **(implemented)**
- The phase is computed as `2π·f·(n / fs) + φ` with `time_origin = 0`, in double precision, so both
  languages agree to about 1e-12 for phases up to ~1e4 radians. Long tones accumulate rounding in the
  argument; see `docs/testing.md` for the tolerance this implies. **(implemented)**

## Power, amplitude, and dB

- **Power of a sample sequence** is the mean of `|x[n]|²` over the sequence, in "sample units
  squared". Nothing is divided by an impedance unless the signal's units say volts and an impedance
  is given. **(implemented)**
- **RMS** is `sqrt(mean |x|²)`. **Peak power** is `max |x|²`; **peak amplitude** is `max |x|`.
  **(implemented)**
- **PAPR** is `10·log10(peak power / mean power)` in dB. A constant-envelope signal (complex tone,
  ±1 square) has 0 dB; a real sine has 3.0103 dB. **CCDF** will use the same instantaneous power
  `|x|²`. **(implemented for PAPR)**
- **DC offset** is the complex mean of the samples (real mean for real input). **(implemented)**
- **dB from a power ratio:** `10·log10(r)`. **dB from an amplitude ratio:** `20·log10(r)`. Zero gives
  −∞; a negative ratio is an error (`ValueError` / `ArgumentOutOfRangeException`), never NaN.
  **(implemented)**
- **dBm** is power relative to 1 mW: `10·log10(P / 1e-3 W)`. **dBW** is relative to 1 W.
  **(implemented for dBm)**
- **Voltage and power:** `P = Vrms² / R`. The reference impedance `R` defaults to **50 Ω** and is
  always a named parameter, never hidden. A sine of peak `Vp` has `Vrms = Vp / √2`. **(implemented)**
- **dBc** is power relative to a named carrier measurement in the same result. A dBc number never
  travels without saying which carrier it is relative to. **(defined)**
- **dBFS:** `10·log10(mean |x|² / FS²)`, where `FS` is the full-scale amplitude (1.0 unless given).
  So a complex tone of amplitude FS is **0 dBFS** and a real sine of peak FS is **−3.01 dBFS**.
  This is the RF/IQ convention. It is **not** the AES17 audio convention, where a full-scale sine is
  0 dBFS; if audio support needs AES17 it gets its own explicitly named function. **(defined)**

## Spectra

Decided in [ADR 0006](adr/0006-fft-windows-spectra.md). Python: `signalforge.spectral`; C#:
`SignalForge.Spectral`.

- **FFT:** forward transform unnormalized, `X[k] = Σ x[n]·e^{−j2πkn/N}`; inverse scaled by `1/N`.
  This is NumPy's default (`norm="backward"`). Any length `N ≥ 1`. **(implemented)**
- **Frequency axis** (`fft_frequencies(n, sample_rate, shifted)`): unshifted, bin `k` is at
  `k·fs/N` for `k ≤ ⌊(N−1)/2⌋` and `(k−N)·fs/N` above that (NumPy `fftfreq` order). Shifted, index
  `i` is at `(i − ⌊N/2⌋)·fs/N`, ascending from `−fs/2` (even `N`) to just under `+fs/2` (NumPy
  `fftshift` order). Frequencies are baseband; add `center_frequency` for absolute frequency.
  **(implemented)**
- **Windows** (`window(name, n, symmetric=False, beta=None)`): with `D = N` (periodic, the default,
  for spectral analysis) or `D = N − 1` (symmetric, for filter design), `n = 0 … N−1`:
  - cosine sums `w[n] = Σₖ (−1)ᵏ·aₖ·cos(2πkn/D)`:
    `rectangular` (a₀ = 1), `hann` (0.5, 0.5), `hamming` (0.54, 0.46),
    `blackman` (0.42, 0.5, 0.08), `blackman_harris` (0.35875, 0.48829, 0.14128, 0.01168),
    `flattop` (0.21557895, 0.41663158, 0.277263158, 0.083578947, 0.006947368; the five-term
    flat-top from D'Antona and Ferrero, *Digital Signal Processing for Measurement Systems*, 2006);
  - `kaiser`: `w[n] = I₀(β·√(1 − (2n/D − 1)²)) / I₀(β)`, `0 ≤ β ≤ 700` required (and only
    allowed here); I₀(β) overflows a double just above β = 713. The limit is `KAISER_MAX_BETA` /
    `Spectral.KaiserMaxBeta`.
  - `N = 0` gives an empty window; `N = 1` gives `[1]`. Unknown names raise.
  **(implemented)**
- **Window figures** (`window_stats(w)`): coherent gain `CG = Σw / N` (a tone at a bin center reads
  `CG` times its amplitude); equivalent noise bandwidth in bins `ENBW = N·Σw² / (Σw)²`. Hann has
  CG 0.5 and ENBW exactly 1.5. **(implemented)**
- **PSD** (`welch_psd(samples, sample_rate, nperseg=None, noverlap=None, window="hann",
  one_sided=None, beta=None)`), Welch's method (`beta` is the Kaiser β):
  - `nperseg` defaults to the whole input; `noverlap` defaults to `⌊nperseg/2⌋`, `0 ≤ noverlap <
    nperseg`. Segments start at `0, step, 2·step, …` with `step = nperseg − noverlap`, as many as fit
    whole: `num_segments = ⌊(L − nperseg)/step⌋ + 1`. No detrending, no zero padding.
  - Each segment is multiplied by the window `w` (periodic, length `nperseg`) and transformed. The
    two-sided PSD is the mean over segments of `|X[k]|² / (fs·Σw²)`, in sample-units²/Hz. Its sum
    times `fs/N` is the mean power of the windowed segments, equal to the signal's mean power for
    the rectangular window and for noise in expectation.
  - Complex input: two-sided, shifted order (frequencies from `fft_frequencies(shifted=True)`).
    Real input: one-sided by default, bins `0 … ⌊N/2⌋` at `k·fs/N`, with every bin doubled except DC
    and, for even `N`, Nyquist. Real input with `one_sided=False` gives the two-sided shifted PSD;
    complex input with `one_sided=True` raises.
  - The result carries `frequencies`, `psd`, `sample_rate`, `nperseg`, `num_segments`,
    `one_sided`, `bin_width = fs/N` and `enbw_hz = ENBW·fs/N` (the resolution bandwidth), and
    `span`: `(0, fs/2)` when one-sided, else none (see Bins as rectangles).
  **(implemented)**
- **PSD units:** W/Hz when the samples are volts and an impedance is known (divide by the
  impedance), otherwise sample-units²/Hz. The functions above work in sample units. **(defined)**
- **Bins as rectangles:** OBW and channel power treat PSD bin `k` (center `f_k`, uniform spacing
  `Δ`) as holding power `PSD_k·Δ` spread evenly over `[f_k − Δ/2, f_k + Δ/2]`. So cumulative power
  is piecewise linear in frequency and band edges are interpolated within a bin. Frequencies must
  be finite, ascending and evenly spaced (relative error ≤ 1e-6), at least two bins, PSD finite
  and ≥ 0.
  - An optional `span = (low, high)` clips every bin's interval to `[low, high]`; a clipped bin
    keeps its whole power, spread over the clipped width. `low ≤ f_0` and `high ≥` the last bin
    center are required. A one-sided PSD needs its `span` `(0, fs/2)`: its DC bin (and Nyquist bin,
    for even `N`) covers only half a bin of positive frequency but holds that bin's full power, so
    without the span the power in `[0, f]` is undercounted near DC and Nyquist.
  **(implemented)**
- **Occupied bandwidth** (`occupied_bandwidth(frequencies, psd, fraction=0.99, span=None)`), the
  ITU-R SM.328 β/2 method: the band outside which lies `(1 − fraction)/2` of the total power on each
  side. With `C(f)` the cumulative power and `P` the total (the running sum of bin powers in
  ascending order, so `C` ends exactly at `P`), `lower` is the `f` where `C(f) = (1 − fraction)/2·P`,
  interpolated within the first bin whose power takes `C` above that, and `upper` the `f` where
  `C(f) = (1 + fraction)/2·P`, within the last bin where `C` starts below it. With `fraction = 1`
  these are the outer edges of the first and last bins with power. `0 < fraction ≤ 1`; `P > 0`
  required. Result: `bandwidth = upper − lower`, `lower`, `upper`, `total_power`, `fraction`.
  **(implemented)**
- **Channel power** (`channel_power(frequencies, psd, low, high, span=None)`): the PSD integrated
  over `[low, high]`, each bin counted by the fraction of its (clipped) width inside. Finite
  `low < high` required. Result in the PSD's power units. **(implemented)**
- Windowed spectra state the window and the correction (coherent gain for tone amplitude, ENBW for
  noise and power) in the result. **(defined)**

## Bits and symbols

- Bits are integers 0 or 1 (`uint8` / `byte`). **(implemented)**
- Bits group into symbols **MSB first**: for a symbol of `k` bits, the first bit in the stream is the
  most significant bit of the symbol index. **(implemented)**
- **QPSK (Gray):** a bit pair `(b0, b1)` maps to `((1 − 2·b0) + j·(1 − 2·b1)) / √2`. So
  `00 → (+1+j)/√2`, `01 → (+1−j)/√2`, `10 → (−1+j)/√2`, `11 → (−1−j)/√2`. Average symbol energy is 1.
  Hard decision takes the sign of I for `b0` and the sign of Q for `b1`; a value of exactly 0 decides
  bit 0. **(implemented)**
- Other constellations are normalized to unit average symbol energy unless a standard says otherwise.
  **(defined)**

## PRBS

- `prbs(order, n)` produces the maximal-length sequence for the ITU-T O.150 polynomials
  (PRBS7 `x⁷+x⁶+1`, PRBS9 `x⁹+x⁵+1`, PRBS11 `x¹¹+x⁹+1`, PRBS15 `x¹⁵+x¹⁴+1`, PRBS20 `x²⁰+x³+1`,
  PRBS23 `x²³+x¹⁸+1`, PRBS31 `x³¹+x²⁸+1`). **(implemented)**
- For a polynomial `xᵐ + xᵏ + 1` the exponents are the shift-register taps: the sequence satisfies
  `a[i] = a[i−m] XOR a[i−k]`. The first `m` output bits are the seed, which defaults to all ones.
  So PRBS7 starts `1111111 000000 1 00000 11…` (worked by hand in
  `vectors/cases/prbs.json`). **(implemented)**
- The output is **not inverted**. O.150 specifies an inverted output for some of these patterns when
  used on a line; an `invert=True` option gives that. Test-equipment "PRBS15" may differ in seed,
  inversion or bit order; never assume two tools' PRBS outputs line up without checking.
  **(implemented)**

## Random numbers

- Every random function takes an explicit seed or generator. Nothing reads global random state.
  **(defined)**
- Python and C# random streams are **not** bit-identical. Cross-language tests compare statistics of
  random signals, or exchange the actual samples as files; they never assume the same seed gives the
  same noise in both languages. **(defined)**
