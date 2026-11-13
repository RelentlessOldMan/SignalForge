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
- Counts (`n`, `num_samples`, `num_bits`, `order`, `seed`, `nperseg`, `noverlap`, `factor`,
  `samples_per_symbol`, `span_symbols`, `block_symbols`, `num_taps`, `up`, `down`, and the link's `num_symbols`,
  `delay_samples`, `preamble_symbols`, `phase_block_symbols`) are integers ≥ 0.
  Python accepts anything with `__index__` (so NumPy integers) and rejects bools and floats, even whole
  ones like `3.0`; C# takes `int`. **(implemented)**
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
- **Spectrogram** (`spectrogram(samples, sample_rate, nperseg, noverlap=None, window="hann",
  one_sided=None, beta=None)`): Welch's segments, each kept instead of averaged. `nperseg` is
  required (`1 ≤ nperseg ≤ L`); `noverlap`, the window, the scaling, the sidedness and the
  frequency axis are exactly as for the PSD above, so row `s` is `welch_psd` of segment `s` alone
  and the mean of the rows is `welch_psd` of the whole input (to rounding).
  - `psd` has one row per segment (`num_segments` rows of `len(frequencies)` bins): Python a 2-D
    array, C# an array of rows.
  - `times[s] = (s·step + nperseg/2) / fs`: the segment's center, in seconds from the first sample
    (add the signal's `time_origin` for absolute time). For even `nperseg` it falls between two
    samples.
  - The result carries `frequencies`, `times`, `psd`, `sample_rate`, `nperseg`, `num_segments`,
    `one_sided`, `bin_width`, `enbw_hz` and `span`, with the PSD's meanings.
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

## Pulse shaping

Decided in [ADR 0007](adr/0007-pulse-shaping-channel-evm.md). Python: `signalforge.dsp`; C#:
`SignalForge.Dsp`.

- **Convolution** (`convolve(x, h)`): full linear convolution, `y[n] = Σₖ h[k]·x[n−k]`, length
  `len(x) + len(h) − 1`; both non-empty. **(implemented)**
- **Upsampling** (`upsample(x, factor)`): each sample followed by `factor − 1` zeros, so the output
  has `len(x)·factor` samples and `y[i·factor] = x[i]`. `factor ≥ 1`. **(implemented)**
- **RRC taps** (`rrc_taps(beta, samples_per_symbol, span_symbols)`): `N = span·sps + 1` taps at
  `t = (n − (N−1)/2) / sps` symbol periods, `n = 0 … N−1`, with
  `h(t) = [sin(πt(1−β)) + 4βt·cos(πt(1+β))] / [πt(1 − (4βt)²)]`, and the limits
  `h(0) = 1 − β + 4β/π` and, where `|4βt| = 1` (tested as `|4β|t| − 1| < 1e-9`),
  `h = (β/√2)·[(1 + 2/π)·sin(π/(4β)) + (1 − 2/π)·cos(π/(4β))]`. Then scaled to **unit energy**,
  `Σh² = 1`. `0 ≤ β ≤ 1`, `sps ≥ 1`, `span ≥ 2` and even (so the center tap is at `t = 0`).
  **(implemented)**
- **Pulse shaping** (`pulse_shape(symbols, taps, samples_per_symbol)`): `convolve(upsample(symbols,
  sps), taps)`, length `len(symbols)·sps + N − 1`. Symbol `k` peaks at sample `k·sps + (N−1)/2`.
  **(implemented)**
- **Matched filter:** convolve with the same taps (RRC is real and symmetric). After shaping and
  matched filtering, symbol `k` is at sample `k·sps + N − 1`, with unit gain (unit-energy taps).
  **(implemented)**

## FIR filters

Decided in [ADR 0010](adr/0010-fir-design-streaming.md). Python: `signalforge.dsp`; C#:
`SignalForge.Dsp` and `SignalForge.FirFilter`.

- **Windowed-sinc design.** `N = num_taps` taps, `n = 0 … N−1`, centered at `t = n − (N−1)/2`;
  frequencies in Hz at `sample_rate = fs`, written normalized as `ν = f/fs`; `sinc(x) = sin(πx)/(πx)`,
  `sinc(0) = 1`. Each design is the ideal response `d[n]`, times the **symmetric** window
  `w = window(name, N, symmetric=True, beta)` (default `hamming`), then scaled so its zero-phase
  gain `A(f) = Σ h[n]·cos(2π·f·t/fs)` (real, because the taps are symmetric) is exactly 1 at a
  reference frequency:
  - `fir_lowpass(num_taps, cutoff, sample_rate, window="hamming", beta=None)`:
    `d = 2ν_c·sinc(2ν_c·t)`; unit gain at `f = 0` (so `Σh = 1`). `N ≥ 1`.
  - `fir_highpass(num_taps, cutoff, sample_rate, window="hamming", beta=None)`:
    `d = sinc(t) − 2ν_c·sinc(2ν_c·t)`; unit gain at `fs/2`. `N` must be **odd** (an even-length
    symmetric filter has a zero at `fs/2`).
  - `fir_bandpass(num_taps, low, high, sample_rate, window="hamming", beta=None)`:
    `d = 2ν_h·sinc(2ν_h·t) − 2ν_l·sinc(2ν_l·t)`; unit gain at the band center `(low + high)/2`.
    `N ≥ 1`.
  - Frequencies satisfy `0 < cutoff < fs/2` and `0 < low < high < fs/2`, all finite. `beta` is the
    Kaiser window's, and only allowed with `window="kaiser"` (as for `window`).
  - If `|A(ref)|` before scaling is not above `1e-6·Σ|h|`, the design raises: the taps are all
    zero (the symmetric Hann window of length 2 is exactly `[0, 0]`), or too few for the band,
    so the scaling would blow up.
  - The taps are linear phase with a delay of `(N−1)/2` samples.
- **Kaiser parameters** (`kaiser_parameters(attenuation_db, transition_width, sample_rate)`,
  returns `(num_taps, beta)`): Kaiser's formulas as given in Oppenheim and Schafer,
  *Discrete-Time Signal Processing* (3rd ed., the Kaiser window design method), with
  `A = attenuation_db` and `Δω = 2π·transition_width/fs`:
  - `β = 0.1102·(A − 8.7)` for `A > 50`; `0.5842·(A − 21)^0.4 + 0.07886·(A − 21)` for
    `21 ≤ A ≤ 50`; `0` for `A < 21`;
  - order `M = ⌈(A − 8)/(2.285·Δω)⌉`, at least 0, and `num_taps = M + 1`.
  - `A > 0`, `0 < transition_width < fs/2`, all finite; a `num_taps` above 2³¹ − 1 raises. For a
    high-pass, round `num_taps` up to odd.
- **Frequency response** (`fir_response(taps, frequencies, sample_rate)`): the complex
  `H(f) = Σ h[n]·e^(−j2π·f·n/fs)` at each frequency (`n` from 0, so it includes the delay).
  Real taps, non-empty and finite; frequencies finite.
- **Streaming filter** (`FirFilter(taps)`, method `process(chunk)`, `reset()`): causal direct
  form, `y[n] = Σₖ h[k]·x[n−k]` over the concatenation of every chunk since the start or the last
  reset, with `x` zero before the first sample. Each call returns as many samples as it is given,
  so the outputs of any split of a signal concatenate to the first `len(x)` samples of
  `convolve(x, h)`. Taps are real, non-empty and finite. The first non-empty chunk fixes the
  filter as real or complex; a chunk of the other kind raises, until `reset()`. An empty chunk
  returns an empty output and changes nothing.

## IIR filters

Decided in [ADR 0014](adr/0014-iir-filters.md). Python: `signalforge.dsp`; C#: `SignalForge.Dsp`
and `SignalForge.IirFilter`.

- **Second-order sections.** An IIR filter is a cascade of sections, each a row
  `[b0, b1, b2, a0, a1, a2]` with transfer function
  `H_i(z) = (b0 + b1·z⁻¹ + b2·z⁻²)/(a0 + a1·z⁻¹ + a2·z⁻²)`; the filter is their product, applied in
  row order. Python holds them as a float array of shape `(sections, 6)`, C# as `double[][]`, one
  array of 6 per section. A valid cascade has at least one section, every value finite and every
  `a0 ≠ 0`; each row is divided by its `a0` on the way in, so a function or filter given a cascade
  works on a copy with `a0 = 1`. Stability is not checked.
- **Butterworth design** (`butterworth_lowpass(order, cutoff, sample_rate)` and
  `butterworth_highpass(order, cutoff, sample_rate)`): the analog Butterworth filter of that order,
  its cutoff prewarped to `Ω_c = 2·fs·tan(π·f_c/fs)`, through the bilinear transform
  `s = 2·fs·(1 − z⁻¹)/(1 + z⁻¹)`. So `|H(f)|² = 1/(1 + (tan(πf/fs)/K)^(2·order))` for the
  low-pass and `1/(1 + (K/tan(πf/fs))^(2·order))` for the high-pass, `K = tan(π·f_c/fs)`: exactly
  `1/2` (−3.01 dB) at the cutoff. The sections, with analog pole angles
  `θ_k = π/2 + π(2k + 1)/(2·order)`, `k = 0 … order − 1`:
  - for an odd order, first a first-order section from the real pole (`k = (order − 1)/2`):
    zero at `z = −1` (low-pass) or `z = 1` (high-pass), `b2 = a2 = 0`;
  - then one section per conjugate pole pair `k` and `order − 1 − k`, for `k = ⌊order/2⌋ − 1`
    down to 0 (in order of rising Q, the sharpest last), with a double zero at `z = −1` (low-pass)
    or `z = 1` (high-pass);
  - each section with `a0 = 1` and unit gain at `f = 0` (low-pass) or `fs/2` (high-pass). With
    `1/Q = 2·sin(π(2k + 1)/(2·order))` and `D = K² + K/Q + 1`, a low-pass pair is
    `b = K²·[1, 2, 1]/D`, `a = [1, 2(K² − 1)/D, (K² − K/Q + 1)/D]`, a high-pass pair the same `a` with
    `b = [1, −2, 1]/D`; the first-order low-pass is `b = K·[1, 1, 0]/(K + 1)`,
    `a = [1, (K − 1)/(K + 1), 0]`, the high-pass the same `a` with `b = [1, −1, 0]/(K + 1)`.
  - `order` is an integer `≥ 1`; `0 < cutoff < fs/2`, finite.
- **Frequency response** (`sos_response(sos, frequencies, sample_rate)`): the complex
  `H(f) = Π_i H_i(e^(j2π·f/fs))` at each frequency. Frequencies finite.
- **Streaming filter** (`IirFilter(sos)`, method `process(chunk)`, `reset()`, property `sections`,
  a copy with `a0 = 1`): each section is the causal difference equation
  `y[n] = b0·x[n] + b1·x[n−1] + b2·x[n−2] − a1·y[n−1] − a2·y[n−2]` (after dividing by `a0`), with
  zero initial state, the sections in cascade, over the concatenation of every chunk since the start
  or the last reset. How each language arranges the arithmetic (direct form I, transposed direct
  form II) is its own; results agree to rounding. Otherwise as `FirFilter`: each call returns as
  many samples as it is given, the first non-empty chunk fixes the filter as real or complex until
  `reset()`, and an empty chunk changes nothing.

## Resampling

Decided in [ADR 0011](adr/0011-resampling.md). Python: `signalforge.dsp`; C#: `SignalForge.Dsp`.

- **Rational resampling** (`resample(x, up, down, taps=None)`): `up, down ≥ 1` are reduced by
  their greatest common divisor to `L, M`. With `u` the zero-stuffed `x` (`u[n·L] = x[n]`, other
  samples 0, and `u` zero outside `0 … len(x)·L − 1`), taps `h` of **odd** length `N` and
  `D = (N − 1)/2`:
  `y[m] = L·Σₖ h[k]·u[m·M + D − k]` for `m = 0 … ⌈len(x)·L/M⌉ − 1`.
  Output sample `m` is at input time `m·M/L` (input sample periods). `x` is real or complex (the
  output matches); taps are real, non-empty, finite and odd in length; `x` is non-empty.
- **Default taps** (`resample_taps(up, down)`): with `R = max(L, M)` after reduction,
  `fir_lowpass(20·R + 1, 1/(2R), 1)` (Hamming). When `taps` is omitted, `resample` uses these.
  `resample_taps` raises when `R = 1` (the cutoff would be `fs/2`); `resample` with `L = M = 1`
  and no taps returns a copy of `x`.
- `interpolate(x, factor, taps=None)` is `resample(x, factor, 1, taps)`; `decimate(x, factor,
  taps=None)` is `resample(x, 1, factor, taps)`.

## Channel

Python: `signalforge.channel`; C#: `SignalForge.Channel`.

- **AWGN** (`awgn(samples, es_n0_db, samples_per_symbol=1, *, seed, signal_power=None)`): adds
  circular complex Gaussian noise of total variance `σ² = P·sps / 10^(Es/N0 / 10)` (each of I and Q
  gets `σ²/2`), where `P` is `signal_power` or, if not given, the measured mean `|x|²` of the
  samples. So Es is the energy per symbol, `P·sps`, and N0 is the noise power per complex sample.
  Complex samples only. Es/N0 must be finite and the variance must be finite (so a very low
  Es/N0, around −3000 dB, is rejected); a very high one gives zero noise. The seed (an integer, or in Python a `numpy.random.Generator`; in C# an
  integer or a `Random`) is required. **(implemented)**
- **Frequency offset** (`frequency_offset(samples, offset_hz, sample_rate, phase=0)`):
  `y[n] = x[n]·e^{j(2π·Δf·n/fs + φ)}`; a positive offset moves the spectrum up (see Complex
  baseband). **(implemented)**

## Synchronization

Decided in [ADR 0008](adr/0008-block-synchronization.md). Python: `signalforge.sync`; C#:
`SignalForge.Sync`. All are block estimators over finite complex samples; they estimate, they do
not correct. Where a sum below is exactly zero there is no information and the estimate is 0. `arg`
is in `(−π, π]`. The timing sum uses `e^{−j2π(n mod sps)/sps}`, the same value with a small
argument. The estimates do not depend on the input's scale: each implementation first
multiplies the block by the power of two that brings its largest real or imaginary part into
`[0.5, 1)` (exact), so `|z|⁴` and `|y|²` neither overflow nor underflow for any finite input.

- **Timing offset** (`timing_offset(samples, samples_per_symbol)`), Oerder–Meyr: with
  `S = Σₙ |y[n]|²·e^{−j2πn/sps}`, `τ = −sps·arg(S)/(2π)`, wrapped into `[0, sps)` (add `sps` if
  negative; a result that rounds to `sps` is 0). The symbol instants are at `τ + m·sps`; for
  `|y|² = A + B·cos(2π(n − τ)/sps)` over whole symbols and `sps ≥ 3` the estimate is exactly `τ`
  (at `sps = 2` the line aliases onto its own image). `sps ≥ 2`, at least one sample.
  **(implemented)**
- **QPSK frequency offset** (`qpsk_frequency_offset(symbols, symbol_rate)`): with `w = z⁴`,
  `S = Σₖ₌₁ w[k]·conj(w[k−1])`, `Δf = arg(S)·symbol_rate / (8π)`, in `(−Rs/8, Rs/8]`. At least two
  symbols. Correct with `frequency_offset(symbols, −Δf, symbol_rate)`. **(implemented)**
- **QPSK phase offset** (`qpsk_phase_offset(symbols)`): `φ = arg(−Σ z⁴) / 4`, in `(−π/4, π/4]`;
  the true phase is `φ + m·π/2`. Correct by multiplying by `e^{−jφ}`
  (`frequency_offset(symbols, 0, 1, −φ)`). At least one symbol. **(implemented)**
- **QPSK block phases** (`qpsk_block_phases(symbols, block_symbols)`): block `b` holds symbols
  `b·B … min((b+1)·B, N) − 1` (the last block may be shorter), and `θ_b` is its
  `qpsk_phase_offset`. Unwrapped: `φ₀ = θ₀`, and `φ_b = θ_b + (π/2)·round((φ_{b−1} − θ_b)/(π/2))`,
  rounding half to even. Returns one value per block. `block_symbols ≥ 1`, at least one symbol.
  On `z_k = a_k·e^{j(θ + ωk)}` each block gives the phase at its middle, `θ + ω·(first + last)/2`,
  as long as consecutive blocks differ by less than π/4. **(implemented)**

## EVM and BER

Python: `signalforge.metrics`; C#: `SignalForge.Metrics`.

- **EVM** (`evm(measured, reference)`): with `e = measured − reference`,
  `rms = √(Σ|e|² / Σ|reference|²)`, `rms_percent = 100·rms`, `rms_db = 20·log10(rms)` (−∞ for a
  perfect match), `peak = max|e| / √(mean |reference|²)`, `peak_index` its first index, and
  `num_symbols`. Equal non-zero lengths, finite values, reference power `> 0`. **(implemented)**
- **QPSK BER theory** (`qpsk_ber_theory(eb_n0_db)`): Gray-coded QPSK in AWGN,
  `Pb = ½·erfc(√(Eb/N0))`, Eb/N0 linear from dB; where that overflows (above about 3080 dB) it
  is infinite and `Pb = 0`. `−∞` dB gives ½, NaN is rejected. For QPSK `Es = 2·Eb`, so
  `Es/N0 [dB] = Eb/N0 [dB] + 10·log10(2)`. **(implemented)**

## QPSK link

Decided in [ADR 0009](adr/0009-qpsk-link-report.md). Python: `signalforge.link`; C#:
`SignalForge.Link`. `qpsk_link(config)` runs one block and returns `QpskLinkReport`.

- **Config** (`QpskLinkConfig`, defaults in brackets): `num_symbols` (≥ 2), `eb_n0_db` [none: no
  noise], `symbol_rate` [1000] Hz, `samples_per_symbol` [4] (≥ 2), `rolloff` [0.35],
  `span_symbols` [10], `delay_samples` [0], `frequency_offset_hz` [0], `phase` [0] rad,
  `preamble_symbols` [32] (1 to `num_symbols`), `phase_block_symbols` [32] (≥ 1), `prbs_order`
  [15], `seed` [0]. Numbers must be finite. **(implemented)**
- **Transmitter:** `bits = prbs(prbs_order, 2·num_symbols)`, `a = qpsk_map(bits)`,
  `h = rrc_taps(rolloff, sps, span_symbols)`, `tx` = `delay_samples` zeros followed by
  `pulse_shape(a, h, sps)`. **(implemented)**
- **Channel:** `frequency_offset(tx, frequency_offset_hz, symbol_rate·sps, phase)`, then, with
  `eb_n0_db`, `awgn(·, eb_n0_db + 10·log10 2, sps, seed, signal_power = 1/sps)` (the shaped
  signal's nominal power). **(implemented)**
- **Receiver**, with `N = num_symbols`, `P = preamble_symbols`, `B = phase_block_symbols`:
  1. `y = convolve(rx, h)`; `τ = timing_offset(y, sps)`; `r = y[round(τ) mod sps :: sps]`
     (round half to even).
  2. `f₁ = qpsk_frequency_offset(r, symbol_rate)`; `c = frequency_offset(r, −f₁, symbol_rate)`.
  3. Frame start `k₀`: the first `k` in `0 … len(r) − N` that maximizes
     `|Σ_{i<P} conj(a[i])·c[k+i]|`.
  4. `z = frequency_offset(r[k₀ : k₀+N], −f₁, symbol_rate)`; `φ_b = qpsk_block_phases(z, B)` at
     `x_b` = the middle of block `b`, `(first + last)/2`.
  5. With more than one block, the least-squares line `φ ≈ φ₀ + s·x`:
     `s = Σ(x−x̄)(φ−φ̄) / Σ(x−x̄)²`, `φ₀ = φ̄ − s·x̄`; with one block, `s = 0` and `φ₀ = φ_0`.
  6. `m = round(arg(Σ_{i<P} conj(a[i])·z[i]·e^{−j(φ₀ + s·i)}) / (π/2))` (half to even);
     the phase is `φ = φ₀ + m·π/2` wrapped into `(−π, π]`, and the frequency
     `f = f₁ + s·symbol_rate/(2π)`.
  7. The symbols are `frequency_offset(r[k₀ : k₀+N], −f, symbol_rate, −φ)`; they are compared with
     `a` by `evm` and, after `qpsk_demap_hard`, with `bits` by `bit_errors`. The preamble counts.
  **(implemented)**
- **Report** (`QpskLinkReport`): `config`, `timing_offset` (τ, samples), `frame_start` (`k₀`,
  symbols into `r`), `frequency_offset_hz` (`f`), `phase_offset` (`φ`, rad: the carrier phase at the
  frame's first symbol), `evm` (an EVM record), `bit_errors` (an error-count record), `ber_theory`
  (`qpsk_ber_theory(eb_n0_db)`, or none without noise). **(implemented)**
- **JSON** (`to_json()` / `ToJson()`): an object with exactly those field names, nested records as
  objects, none as `null`, integers as integers, and non-finite numbers as the strings `"inf"`,
  `"-inf"`, `"nan"`. Compare reports as JSON values, not text. **(implemented)**
- For a noiseless link the true values are known from the channel: the first symbol's peak is at
  `y[L − 1 + delay_samples]` (`L` = number of taps), so `frame_start = ⌊(L − 1 + delay)/sps⌋`, and
  `φ = phase + 2π·frequency_offset_hz·(delay + (L−1)/2)/(symbol_rate·sps)`, the carrier phase at
  the middle of the first transmitted pulse. Truncated taps and an offset applied before the matched
  filter leave a little inter-symbol interference, so these hold to a tolerance, not exactly.

## Signal files

Decided in [ADR 0012](adr/0012-signal-files.md). Python: `signalforge.files`; C#:
`SignalForge.SignalFiles`. Implemented from the SigMF format description, not from its text.

- **Data types** are named `<kind><type>[_<order>]`: kind `c` (complex, interleaved I then Q) or
  `r` (real); type `f64`, `f32`, `i32`, `i16` or `i8`; order `le` or `be`, which `i8` omits and
  every other type requires. Anything else (unsigned types, `f16`, a missing or extra order) is
  rejected. **(implemented)**
- **Integer scaling**: code `c` of a `b`-bit type is the sample `c / 2^(b−1)`, so full scale is
  1.0 (units `"FS"` if the caller wants to say so). Writing, a sample becomes
  `round(x·2^(b−1))`, rounding half to even; a non-finite sample or a code outside
  `−2^(b−1) … 2^(b−1) − 1` is rejected (nothing is clipped silently, so `+1.0` itself cannot be
  written). Complex samples scale each part. **(implemented)**
- **Floats** are stored as IEEE binary64 or binary32 in the given byte order; writing `f32` rounds
  to nearest even, and a value beyond its range becomes ±inf. NaN and ±inf are stored as they are.
  Reading always returns `float64` / `complex128` (`double` / `Complex`). **(implemented)**
- `encode_samples(x, datatype)` gives the bytes, `decode_samples(data, datatype)` the samples; the
  byte count must be a whole number of samples. A real datatype needs real samples and a complex
  one complex samples. In C# the kind is the type argument (`DecodeSamples<double>`), and a
  datatype of the other kind is rejected. **(implemented)**
- **Recording** (`write_sigmf(path, signal, datatype)`, `read_sigmf(path)`): two files,
  `<base>.sigmf-meta` (UTF-8 JSON) and `<base>.sigmf-data` (the raw samples, nothing else). `path`
  is the base, or either file's name. Written meta:
  - `global`: `core:datatype`, `core:version` (`"1.2.0"`), `core:sample_rate`, `core:extensions`
    (one entry: name `signalforge`, version `1.0.0`, optional), `signalforge:time_origin`, then
    `signalforge:units` and `signalforge:impedance` when they are set, `signalforge:metadata` (an
    object) for metadata keys without a `:`, and every metadata key with a `:` as its own field.
  - `captures`: one, `{"core:sample_start": 0, "core:frequency": center_frequency}`.
  - `annotations`: empty.
  Rejected on write: a datatype of the other kind, a non-finite `center_frequency` or
  `time_origin`, metadata that is not JSON (strings, finite numbers, bools, null, lists, string-keyed
  objects), and a metadata key that would replace a field above (`core:datatype`, `core:version`,
  `core:sample_rate`, `core:extensions`, `core:num_channels`, `core:dataset`,
  `core:metadata_only`, or anything `signalforge:`). **(implemented)**
- **Reading** inverts that. `core:datatype`, `core:version` (a string starting `1.`) and
  `core:sample_rate` (positive, finite) are required. Rejected: `core:num_channels` other than the
  integer 1, `core:dataset` or `core:metadata_only`, a capture whose `core:header_bytes` is not the
  integer 0, captures with
  different `core:frequency` (a missing one is 0), a data file that is not a whole number of
  samples, JSON with duplicate keys or the non-standard `NaN`/`Infinity`. Other global fields go to
  `metadata` under their own names; annotations and the rest of each capture are not read.
  JSON numbers without a fraction or exponent are integers (`int` / `long`), others floats;
  writing, a float always gets a fraction or an exponent (`2.0`, not `2`), so the kind survives a
  trip through the other language. A missing or unreadable file is an OS error (`OSError` /
  `IOException`), not `invalid_argument`. **(implemented)**

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
