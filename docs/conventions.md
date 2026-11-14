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
- **Multitone** (`multitone(sample_rate, num_samples, frequencies, amplitudes=None, phases=None,
  complex=True)`; C# `Multitone` and `RealMultitone`): the sum, in the order given, of
  `tone(sample_rate, num_samples, f_k, A_k, φ_k)` over the tones `k`. `amplitudes` (peak, default
  all 1) and `phases` (radians, default all 0) have one value per frequency; at least one
  frequency; every value finite.
- **Newman phases** (`newman_phases(count)`): `φ_k = π·k²/K` for `k = 0 … K − 1`, `K = count ≥ 1`.
  Newman's rule for a multitone of equally spaced, equal-amplitude tones with a low crest factor.
- **Linear chirp** (`chirp(sample_rate, num_samples, start, stop, amplitude=1, phase=0,
  complex=True)`; C# `Chirp` and `RealChirp`): the instantaneous frequency rises (or falls)
  linearly from `start` Hz at the first sample to `stop` Hz at `T = num_samples/fs`, one sample
  after the last, so a chirp of `N` samples followed by another from `stop` continues without a
  frequency jump. Samples `A·e^(jθ[n])` (or `A·cos θ[n]`) with
  `θ[n] = 2π·(start·t + (stop − start)·t²/(2T)) + φ`, `t = n/fs`. With `num_samples = 0` the result
  is empty. Frequencies, amplitude and phase finite.
- **Pulse train** (`pulse_train(num_samples, period, width, amplitude=1, delay=0)`, real): in whole
  samples, `x[n] = A` when `(n − delay) mod period < width` and 0 otherwise, `mod` the floored
  modulo (non-negative for a negative `n − delay`). `period ≥ 1`, `0 ≤ width ≤ period`, `delay`
  any integer, `A` finite.
- The tone, multitone and chirp also need finite frequencies, amplitudes and phases.

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
  one_sided=None, beta=None, detrend="none", average="mean", nfft=None)`), Welch's method (`beta`
  is the Kaiser β). Below, `N = nperseg` and `M = nfft`:
  - `nperseg` defaults to the whole input; `noverlap` defaults to `⌊nperseg/2⌋`, `0 ≤ noverlap <
    nperseg`. Segments start at `0, step, 2·step, …` with `step = nperseg − noverlap`, as many as fit
    whole: `num_segments = ⌊(L − nperseg)/step⌋ + 1`.
  - `nfft` defaults to `nperseg`; `nfft ≥ nperseg` (otherwise it raises). Each windowed segment is
    padded with `M − N` zeros at its end and transformed at length `M`: the same spectrum sampled
    on a finer grid, no new resolution.
  - `detrend` acts on each segment `x[0 … N−1]` before the window: `"none"` leaves it;
    `"constant"` subtracts its mean `m = Σx/N`; `"linear"` subtracts its least-squares line
    `m + b·(n − c)`, `c = (N−1)/2`, `b = Σ(n − c)·x[n] / Σ(n − c)²` (`b = 0` when `N = 1`). Complex
    segments use the same formulas on complex values (real and imaginary parts fitted apart).
    Anything else raises. C#: `Detrend.None`, `Detrend.Constant`, `Detrend.Linear`.
  - Each segment is multiplied by the window `w` (periodic, length `nperseg`) and transformed. The
    two-sided PSD is the average over segments of `|X[k]|² / (fs·Σw²)`, in sample-units²/Hz (the
    scale does not depend on `M`). Its sum times `fs/M` is the mean power of the windowed segments
    (Parseval at length `M`), equal to the signal's mean power for the rectangular window and for
    noise in expectation.
  - `average` is `"mean"` (the default) or `"median"`; anything else raises. The median is taken
    per bin over the `K` segments (for even `K`, the mean of the two middle values), then divided
    by `b(K)`, the expected median of `K` independent unit-mean exponential values, so that for
    Gaussian noise in non-overlapping segments it is unbiased like the mean:
    `b(K) = Σ_{i=m+1}^{K} 1/i` for odd `K = 2m+1`, and `b(K) = Σ_{i=m+1}^{K} 1/i + 1/K` for even
    `K = 2m` (`b(1) = b(2) = 1`, `b(3) = 5/6`). It is applied to the two-sided values, before
    one-sided doubling. The median resists bursts that the mean spreads into every bin. The
    correction is for noise: a steady tone has the same power in every segment, so its median is
    that power and the result reads `1/b(K)` too high (`1/ln 2 ≈ 1.44` for large `K`). C#:
    `WelchAverage.Mean`, `WelchAverage.Median`.
  - Complex input: two-sided, shifted order (frequencies from `fft_frequencies(shifted=True)`).
    Real input: one-sided by default, bins `0 … ⌊M/2⌋` at `k·fs/M`, with every bin doubled except DC
    and, for even `M`, Nyquist. Real input with `one_sided=False` gives the two-sided shifted PSD;
    complex input with `one_sided=True` raises.
  - The result carries `frequencies`, `psd`, `sample_rate`, `nperseg`, `nfft`, `num_segments`,
    `one_sided`, `bin_width = fs/M` (the bin spacing) and `enbw_hz = ENBW·fs/N` (the resolution
    bandwidth, set by the window and `nperseg` alone), and `span`: `(0, fs/2)` when one-sided, else
    none (see Bins as rectangles).
  **(implemented)**
- **Spectrogram** (`spectrogram(samples, sample_rate, nperseg, noverlap=None, window="hann",
  one_sided=None, beta=None, detrend="none", nfft=None)`): Welch's segments, each kept instead of
  averaged. `nperseg` is required (`1 ≤ nperseg ≤ L`); `noverlap`, the detrending, the window, the
  zero padding, the scaling, the sidedness and the frequency axis are exactly as for the PSD above,
  so row `s` is `welch_psd`
  of segment `s` alone and the mean of the rows is `welch_psd` of the whole input (to rounding).
  - `psd` has one row per segment (`num_segments` rows of `len(frequencies)` bins): Python a 2-D
    array, C# an array of rows.
  - `times[s] = (s·step + nperseg/2) / fs`: the segment's center, in seconds from the first sample
    (add the signal's `time_origin` for absolute time). For even `nperseg` it falls between two
    samples.
  - The result carries `frequencies`, `times`, `psd`, `sample_rate`, `nperseg`, `nfft`,
    `num_segments`, `one_sided`, `bin_width`, `enbw_hz` and `span`, with the PSD's meanings.
  **(implemented)**
- **Lomb-Scargle periodogram** (`lomb_scargle(times, values, frequencies, center=True,
  normalization="standard")`, [ADR 0059](adr/0059-lomb-scargle.md)), for unevenly sampled real
  data. `times` and `values` are finite reals of the same length `N ≥ 2` (times in any order,
  repeats allowed); `frequencies` are finite and `> 0`, in Hz (cyclic), and may be empty. With
  `y = values − mean(values)` when `center` (else `y = values`), for each frequency `f`,
  `ω = 2πf`:
  - `τ = atan2(Σ sin 2ωtₙ, Σ cos 2ωtₙ) / (2ω)` (any τ serves when both sums are 0);
  - `C = Σ yₙ cos ω(tₙ − τ)`, `S = Σ yₙ sin ω(tₙ − τ)`, `CC = Σ cos² ω(tₙ − τ)`,
    `SS = Σ sin² ω(tₙ − τ)`;
  - `P = ½(C²/CC + S²/SS)`, where a term whose denominator is below `1e-12·N` is 0.
  - `normalization="power"` returns `P` (value units squared); `"standard"` returns `2P / Σyₙ²`,
    which needs `Σyₙ² > 0`. Anything else raises.
  `P` equals `½(Σy² − χ²_min)`, with `χ²_min` the residual of the least-squares fit of
  `a cos ωt + b sin ωt` to `y`; it does not change when every time is shifted by the same amount.
  On `N` even samples with `f` at a bin `k·fs/N` (`0 < k < N/2`), a sinusoid of amplitude `A` at
  that bin gives `P = A²N/4` and standard 1. **(implemented)**
- **Lomb-Scargle false-alarm probability** (`lomb_scargle_false_alarm(power, num_samples,
  num_frequencies=1, center=True)`, [ADR 0062](adr/0062-lomb-scargle-significance.md)), for the
  standard normalization: `P₁ = (1 − z)^((N − d)/2)` with `d = 3` centered, `2` not (the Beta
  survival of white Gaussian noise at one frequency), then `−expm1(M·log1p(−P₁))` for `M`
  independent frequencies. `z` in `[0, 1]`, integers `N ≥ d + 1` and `M ≥ 1`; otherwise
  `invalid_argument`. Exact when the fitted cosine and sine are orthogonal to the constant (not
  centered, or evenly spaced times at a bin), close otherwise. **(implemented)**
- **Lomb-Scargle frequency grid** (`lomb_scargle_frequencies(times, oversampling=5.0,
  max_frequency=None)`): `T = max(t) − min(t)`, which must be `> 0`; `Δ = 1/(oversampling·T)`
  (that product, then its reciprocal); the frequencies are `k·Δ` for `k = 1 … K`,
  `K = ⌊f_max/Δ + 1e-9⌋`, default `f_max = N/(2T)`. `oversampling` and `f_max` positive and finite,
  times finite (at least 2), `K ≤ 10⁷`; `K = 0` gives an empty grid. **(implemented)**
- **PSD units:** W/Hz when the samples are volts and an impedance is known (divide by the
  impedance), otherwise sample-units²/Hz. The functions above work in sample units. **(defined)**
- **Bins as rectangles:** OBW and channel power treat PSD bin `k` (center `f_k`, uniform spacing
  `Δ`) as holding power `PSD_k·Δ` spread evenly over `[f_k − Δ/2, f_k + Δ/2]`. So cumulative power
  is piecewise linear in frequency and band edges are interpolated within a bin. Frequencies must
  be finite, ascending and evenly spaced (relative error ≤ 1e-6) with a finite spacing, at least
  two bins, PSD finite and ≥ 0. Every bin power `PSD_k·Δ` and their sum must be finite, and every
  bin's (clipped) width must be positive in floating point (half a bin must not round away at the
  bin's frequency); otherwise `invalid_argument`.
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
- **ACPR** (`acpr(frequencies, psd, center, bandwidth, offsets, adjacent_bandwidth=None,
  span=None)`, [ADR 0019](adr/0019-acpr.md)): adjacent channel power ratio. The main channel is
  `[center − B/2, center + B/2]`, `B = bandwidth`; for each offset `o` the lower and upper
  adjacent channels are `[center ∓ o − B_a/2, center ∓ o + B_a/2]`, `B_a = adjacent_bandwidth`
  (default `B`). Each channel's power is its channel power, as above (with the same `span`).
  - Result (`Acpr`): `main_power`, and per offset, in the order given, `lower_power`,
    `upper_power`, `lower_dbc = 10·log10(lower_power/main_power)` and `upper_dbc` likewise
    (computed as a difference of logs, so a tiny ratio does not underflow); an empty adjacent
    channel gives `−∞` dBc.
  - Every channel must lie inside the PSD's frequency range, from the first bin's lower edge to
    the last bin's upper edge (each clipped to `span`); a channel that leaves it would count
    missing spectrum as zero power, so it is `invalid_argument`. A channel edge past the spectrum
    by at most `1e-9` of the widest bin counts as on it (rounding in `center ± offset ± B_a/2`). For a one-sided PSD with span
    `(0, fs/2)` a lower channel below 0 Hz is therefore an error.
  - `center` finite; `bandwidth` and `adjacent_bandwidth` finite and `> 0`; `offsets` a non-empty
    list of finite values `> 0`; `main_power > 0`. Channels may overlap one another.
  **(implemented)**
- Windowed spectra state the window and the correction (coherent gain for tone amplitude, ENBW for
  noise and power) in the result. **(defined)**

## Tone metrics

Decided in [ADR 0015](adr/0015-tone-metrics.md). Python: `signalforge.measurements.tone_metrics`;
C#: `Measurements.ToneMetrics`.

- **Call:** `tone_metrics(samples, sample_rate, window="blackman_harris", beta=None, width=None,
  num_harmonics=5, fundamental=None)`. Real or complex samples, at least two, finite;
  `sample_rate > 0`; `width` and `num_harmonics` non-negative integers; `beta` as for `window`.
  **(implemented)**
- **Spectrum:** `welch_psd(samples, sample_rate, window=window, beta=beta)` with the defaults for
  the rest, so one segment of the whole input: one-sided for real input, two-sided shifted for
  complex. Bin `k` holds power `P_k = PSD_k·bin_width`; its frequency is `f_k`. Every `P_k` must
  be finite (`invalid_argument`: a non-finite sample, or samples so large the spectrum overflows),
  and a bin with `P_k ≤ 10⁻²⁰·Σ P_k` is set to exactly 0: that is FFT rounding error (about
  −320 dB for a clean tone), which would otherwise pick fundamentals and spurs from noise that
  differs between implementations. **(implemented)**
- **Half-width `w`:** `width` if given, else `K` for a `K`-term cosine-sum window (rectangular 1,
  hann and hamming 2, blackman 3, blackman_harris 4, flattop 5) and `⌈√(1 + (β/π)²)⌉` for kaiser.
  **(implemented)**
- **Groups**, formed in this order; a group around bin `c` is the bins `max(c−w, 0) …
  min(c+w, M−1)` (`M` bins in all, no wrap, also for a two-sided spectrum: a complex tone near
  `±fs/2` loses the part of its group beyond the end) that no earlier group took:
  1. **DC:** around the bin nearest 0 Hz.
  2. **Fundamental:** around the unclaimed bin with the largest `P_k` (the first, on a tie), or, if
     `fundamental` is given, the bin nearest it, which must not be in the DC group
     (`invalid_argument`). A given `fundamental` must be finite with `|f| ≤ fs/2`, and `≥ 0` for
     real input; for complex input it is first aliased as `((f + fs/2) mod fs) − fs/2`, so `+fs/2`
     means the bin at `−fs/2`. Its frequency `f1 = Σ P_k·f_k / Σ P_k` over the group.
  3. **Harmonics** `h = 2 … num_harmonics + 1`, in order, each around the bin nearest `h·f1`
     aliased into the spectrum: real input `g = (h·f1) mod fs`, then `fs − g` if `g > fs/2`;
     complex input `((h·f1 + fs/2) mod fs) − fs/2`. `mod` is floored (the result has the sign of
     `fs`).
  4. **Noise:** every bin left.
  - The bin nearest a frequency `f` is `⌊(f − f_0)/bin_width + 0.5⌋`, clipped to `0 … M−1`.
  **(implemented)**
- **Result** (`ToneMetrics`): `fundamental_frequency` (`f1`, Hz), `signal_power` `S` (fundamental
  group), `harmonic_power` `H` (all harmonic groups), `noise_power` `N`, `dc_power` (DC group), all
  in sample units², and
  `snr_db = 10·log10(S/N)`, `sinad_db = 10·log10(S/(N + H))`, `thd_db = 10·log10(H/S)`,
  `enob = (sinad_db − 10·log10 1.5) / (20·log10 2)`.
  `S = 0` is `invalid_argument`; `N = 0` gives `snr_db = +∞`, `H = 0` gives `thd_db = −∞`, and
  `N + H = 0` gives `sinad_db` and `enob` `+∞`. Noise is not scaled for the bins the groups took.
  The four group powers add up to the PSD's total power. **(implemented)**

## Spurs and SFDR

Python: `signalforge.measurements.sfdr`; C#: `Measurements.Sfdr`. Same spectrum, half-width and
groups as the tone metrics (ADR 0015).

- **Call:** `sfdr(samples, sample_rate, window="blackman_harris", beta=None, width=None,
  fundamental=None, num_spurs=1)`, arguments as for `tone_metrics`; `num_spurs ≥ 1`.
  **(implemented)**
- **Groups:** DC, then the carrier (the tone metrics' fundamental), then spurs one at a time: each
  spur is the group around the unclaimed bin with the largest `P_k` (the first, on a tie), until
  `num_spurs` are found, no bin is left, or the largest bin left has zero power. So spurs come
  strongest peak bin first, a harmonic is a spur like any other, and DC is never one.
  **(implemented)**
- **Result** (`Sfdr`): `carrier_frequency` and `carrier_power` (as `fundamental_frequency` and
  `signal_power`), and per spur, in the order found, `spur_frequencies` (the group's power
  centroid), `spur_powers` (the group's power) and `spur_dbc = 10·log10(spur / carrier)`.
  `sfdr_db = −spur_dbc[0]`, in dB below the carrier (negative when a spur is stronger than a
  named carrier); `+∞` and empty arrays when no spur is found. **(implemented)**

## Bits and symbols

- Bits are integers 0 or 1 (`uint8` / `byte`). **(implemented)**
- Bits group into symbols **MSB first**: for a symbol of `k` bits, the first bit in the stream is the
  most significant bit of the symbol index. **(implemented)**
- **QPSK (Gray):** a bit pair `(b0, b1)` maps to `((1 − 2·b0) + j·(1 − 2·b1)) / √2`. So
  `00 → (+1+j)/√2`, `01 → (+1−j)/√2`, `10 → (−1+j)/√2`, `11 → (−1−j)/√2`. Average symbol energy is 1.
  Hard decision takes the sign of I for `b0` and the sign of Q for `b1`; a value of exactly 0 decides
  bit 0. **(implemented)**
- **8-PSK (Gray)** ([ADR 0035](adr/0035-psk8-qam16.md)): three bits, MSB first, form the label
  `m`. Point `p` (0…7) is `e^{jπp/4}` and carries the label `p ⊕ (p >> 1)`, so neighbors differ
  in one bit, around the circle too: `000 → 1`, `001 → e^{jπ/4}`, `011 → j`, `010 → e^{j3π/4}`,
  `110 → −1`, `111 → e^{j5π/4}`, `101 → −j`, `100 → e^{j7π/4}`. Hard decision takes
  `p = ⌊atan2(Q, I)/(π/4) + 1/2⌋ mod 8`; 0 decides `000`. A symbol on a boundary between two
  sectors may decide either way within the rounding of `atan2`. A NaN in either part is
  `invalid_argument`. **(implemented)**
- **16-QAM (Gray)**: four bits `(b0, b1, b2, b3)`, `I` from `(b0, b1)` and `Q` from `(b2, b3)`,
  each `(1 − 2·first)·(3 − 2·second)`: `00 → 3`, `01 → 1`, `11 → −1`, `10 → −3`, divided by `√10`
  for unit average symbol energy. As for QPSK, a first bit of 0 is the positive side. Hard
  decision per component `v`: first bit `v < 0`, second bit `|v| < 2/√10` (that quotient
  evaluated in double precision); so 0 decides `01` and `±2/√10` decide the outer level. A NaN
  in either part is `invalid_argument`.
  **(implemented)**
- **64-QAM (Gray)** ([ADR 0052](adr/0052-qam64.md)): six bits, `I` from `(b0, b1, b2)` and `Q`
  from `(b3, b4, b5)`, each `(1 − 2·b_a)·(4 + (1 − 2·b_b)·(3 − 2·b_c))`: `000 → 7`, `001 → 5`,
  `011 → 3`, `010 → 1`, `110 → −1`, `111 → −3`, `101 → −5`, `100 → −7` (the 16-QAM pattern:
  first bit the sign, the rest a reflected Gray code of the magnitude), times `1/√42` (computed
  once) for unit average symbol energy (each axis averages 21). Hard decision per component `v`,
  with `a = |v|` and the thresholds `T₂ = 2/√42`, `T₄ = 4/√42`, `T₆ = 6/√42` (each quotient in
  double precision): first bit `v < 0`, second `a < T₄`, third `T₂ < a < T₆`. Each bit is 1 only
  strictly inside its region, so a value on a threshold decides bit 0: 0 decides `010`, `T₂`
  decides `010`, `T₄` decides `001`, `T₆` decides `000`. A NaN in either part is
  `invalid_argument`. **(implemented)**
- **Soft demapping** (`qpsk_demap_llr`, `psk8_demap_llr`, `qam16_demap_llr`, `qam64_demap_llr`, each
  `(symbols, noise_variance)`, [ADR 0039](adr/0039-soft-demapping.md)): max-log LLRs, one per
  bit in the hard demapper's order. For bit `i` of a received `y`,
  `LLR = (min_{s: bᵢ=1} |y − s|² − min_{s: bᵢ=0} |y − s|²) / noise_variance` over the
  constellation's points, so **positive means bit 0 is likelier** and the hard decision is the
  sign (0 counts as bit 0). `noise_variance` is `N0 = E|n|²` of the complex noise (both parts
  together), positive and finite. `|y − s|²` is `Δre·Δre + Δim·Δim`. Symbols must be finite.
  The exact LLR, `ln(Σ_{bᵢ=0} e^{−|y−s|²/N0} / Σ_{bᵢ=1} e^{−|y−s|²/N0})`, differs from this by at
  most `ln(M/2)`; for QPSK they are equal, `2√2·Re(y)/N0` and `2√2·Im(y)/N0`. **(implemented)**
- **FSK** ([ADR 0054](adr/0054-fsk.md)): `order` `M` is 2, 4, 8 or 16, `k = log2 M` bits per
  symbol, MSB first, form the label `m` (natural binary), and the label's tone level is
  `a = 2m − (M − 1)` (so −1, +1 for `M = 2`; −3, −1, +1, +3 for `M = 4`).
  `modulation_index` `h` is positive and finite; tone `a` sits at `a·h/2` cycles per symbol, so
  neighboring tones are `h` symbol rates apart.
  - `fsk_modulate(bits, order, samples_per_symbol, modulation_index)`: continuous-phase FSK of
    unit amplitude, `len(bits)/k · sps` samples. Sample `n` (0 … sps − 1) of symbol `i` is
    `e^{jφ}` with `φ = π·h·(S_i + a_i·n/sps)`, where `S_i = a_0 + … + a_{i−1}` (an exact
    integer, `S_0 = 0`) and the expression is evaluated in that order (`a_i·n` as an integer,
    then `/ sps`, then `+ S_i`, then `π·h·`). So the phase starts at 0 and steps by `π·h·a/sps`
    each sample with no jump between symbols. The bit count must be a multiple of `k`;
    `sps ≥ 1`.
  - `fsk_demod_noncoherent(samples, order, samples_per_symbol, modulation_index)`: for each block
    of `sps` samples and each label `m`, `c_m = Σ_n x[n]·e^{−jψ}` with
    `ψ = π·h·(a_m·n/sps)`, and the energy `|c_m|² = re² + im²`; the label with the largest
    energy is decided (on a tie, the smallest label) and written out as `k` bits, MSB first.
    The tones are orthogonal over a block, so the detector is the noncoherent optimum, when `h`
    is a whole number and `sps > h·(M − 1)` (no tone aliases onto another). The sample count
    must be a multiple of `sps`; samples must be finite.
  **(implemented)**
- **OFDM** ([ADR 0060](adr/0060-ofdm.md)): `nfft` `N ≥ 1`, `cp_len` `L` with `0 ≤ L ≤ N`.
  `subcarriers` are distinct integers in `−⌊N/2⌋ … N − 1 − ⌊N/2⌋`, at least one; subcarrier `k`
  is DFT bin `k mod N`, at `k·fs/N`. The default is all `N`, ascending from `−⌊N/2⌋`. With `U`
  used subcarriers:
  - `ofdm_modulate(symbols, nfft, cp_len, subcarriers=None)`: the finite complex symbols, a
    multiple of `U` (possibly none), fill block `b` in order: `X_b[subcarriers[i] mod N] =
    symbols[b·U + i]`, every other bin 0. Each block is `x_b[n] = (1/√N)·Σ_k X_b[k]·e^{j2πkn/N}`
    (`n = 0 … N−1`), sent as `x_b[N−L … N−1]` followed by `x_b[0 … N−1]`; the output is the blocks
    in order, `(N + L)` samples each.
  - `ofdm_demodulate(samples, nfft, cp_len, subcarriers=None)`: the finite complex samples, a
    multiple of `N + L`, split into blocks; each drops its first `L` samples, `Y_b[k] =
    (1/√N)·Σ_n y_b[n]·e^{−j2πkn/N}` of the remaining `N`, and gives `Y_b[subcarriers[i] mod N]`
    for each `i` in order. So `ofdm_demodulate` of `ofdm_modulate` returns the symbols.
  **(implemented)**
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
- **Equiripple design** (`fir_equiripple(num_taps, bands, desired, sample_rate, weights=None,
  grid_density=16, kind="filter")`, [ADR 0024](adr/0024-equiripple-fir.md),
  [ADR 0026](adr/0026-antisymmetric-equiripple.md)): the taps whose amplitude `A(f)` minimizes
  the largest weighted error `max |W(f)·(A(f) − T(f))|` over the bands, **on the grid defined
  here** (the discrete optimum; it is unique). `kind` is one of:
  - `"filter"` (the default): symmetric taps, `h[n] = h[N−1−n]`; `A` is the zero-phase gain
    (as above), the target `T = D_j` and the weight `W = W_j` on band `j`.
  - `"hilbert"` and `"differentiator"`: antisymmetric taps, `h[n] = −h[N−1−n]` (so
    `h[(N−1)/2] = 0` for odd `N`). With `c = (N−1)/2`,
    `H(f) = −j·e^(−j2πfc/fs)·A(f)` and `A(f) = Σ_m 2·h[c + m]·sin(2πmf/fs)` over the offsets
    `m = 1, 2, …, c` (odd `N`) or `½, 3/2, …, c` (even `N`), with `h[c + m]` the tap `m` after the
    centre.
  - `"hilbert"`: `T = D_j`, `W = W_j`. `desired` 1 is the Hilbert transformer: `H = −j` times the
    delay at positive frequencies, which turns `cos` into `sin`.
  - `"differentiator"`: `T(f) = −2π(f/fs)·D_j`, so `H ≈ j·2π(f/fs)·D_j` times the delay, and
    `desired` 1 is the derivative per sample. The error is relative to the slope where
    `D_j ≠ 0`: `W(f) = W_j/(2πf/fs)`; `W = W_j` where `D_j = 0`.
  - Any other `kind` is `invalid_argument`.
  - `bands` is a flat list of edges in Hz, `[b_0, b_1, b_2, b_3, …]`, band `j` being
    `[b_2j, b_2j+1]`; at least one band; `0 ≤ b_0 < b_1 < b_2 < … ≤ fs/2`, finite (bands do not
    touch). `desired` has one finite value per band; `weights` one positive finite value per band
    (default all 1). `1 ≤ num_taps ≤ 1001` (`2 ≤` for the antisymmetric kinds); `grid_density` an
    integer, `1 ≤ grid_density ≤ 64`.
  - `N = num_taps`; every such `A` has the factor `Q`, and `P = A/Q` is a cosine sum of `L`
    terms. Symmetric, odd `N` (type I): `L = (N + 1)/2`, `Q(f) = 1`. Symmetric, even `N`
    (type II): `L = N/2`, `Q(f) = cos(πf/fs)`. Antisymmetric, odd `N` (type III):
    `L = (N − 1)/2`, `Q(f) = sin(2πf/fs)`. Antisymmetric, even `N` (type IV): `L = N/2`,
    `Q(f) = sin(πf/fs)`. Where `Q = 0` on a band (`fs/2` for types II and III, `0` for types III
    and IV), the target there must be 0, else `invalid_argument` (a differentiator's is 0 at 0).
  - **Grid**, in `ν = f/fs`: `Δ = 0.5/(grid_density·L)`. Band `j` with `ν_lo = b_2j/fs`,
    `ν_hi = b_2j+1/fs` gets `m = ⌈(ν_hi − ν_lo)/Δ⌉` intervals and the points
    `ν_lo + (ν_hi − ν_lo)·i/m` for `i = 0 … m − 1`, then `ν_hi` exactly. The points where `Q = 0`
    are dropped (`ν = 0.5` for types II and III, `ν = 0` for types III and IV). Fewer than
    `L + 1` points in all is `invalid_argument`.
  - The problem is then: find `P(ν) = Σ_{k<L} c_k cos(2πkν)` minimizing
    `max |W'(ν)(D'(ν) − P(ν))|` over the grid, with `D' = T/Q`, `W' = W·Q`; and `A = Q·P`. Below,
    `S` is the largest `|W·T|` over the grid, which is `max_j |W_j·D_j|` over the bands with grid
    points (for a differentiator too, since there `|W·T| = W_j·|D_j|`).
  - **Algorithm** (Remez exchange; any method reaching the same optimum agrees). The first
    extremal set, by **reference scaling**: for `L ≤ 16`, the grid indices `⌊i·(G − 1)/L⌋`,
    `i = 0 … L`, of the `G` points. For `L > 16`, first design the same bands with
    `L' = ⌈L/2⌉` (`N' = N − 2(L − L')`, the same type, on its own grid; this rule again for its
    start). If that design is beyond double precision, use the index set above. Otherwise, with
    `s(ν)` the distance along the bands (gaps removed) at each of this grid's points (`s` = 0 at the
    first, then the sum of the steps between neighbours in the same band), interpolated linearly
    in `ν` between them: the smaller design's final set `ν'_0 … ν'_{L'}` gives `s'_i = s(ν'_i)`;
    `t_i` interpolates `s'` linearly at the position `i·L'/L`, `i = 0 … L`; point `i` is the first
    grid index with `s ≥ t_i`, raised to one past point `i − 1` if not above it, and the set is then
    pulled back from the end (point `i` at most `G − 1 − (L − i)`) if it runs off the grid. Each
    iteration, with `x = cos(2πν)` at the set: `γ_i = 1/∏_{j≠i}(x_i − x_j)` (computed from
    logarithms, scaled by a common factor), `δ = Σγ_i D'_i / Σ(−1)^i γ_i/W'_i`,
    `P(x_i) = D'_i − (−1)^i δ/W'_i`, and `P` elsewhere by barycentric interpolation through the
    first `L` points. The new set: every grid point where the error `E = W'(D' − P)` is a
    nonzero local extremum within its band (`E > 0` and not below either in-band neighbour, or
    the mirror for `E < 0`), plus the old set's points, where `E = (−1)^i δ` exactly and which
    count with that sign (`+` for `δ = 0` at even `i`), so the new set always alternates at least
    `L + 1` times; runs of the same sign keep their largest `|E|` (the first of
    equals); while there are more than `L + 1`: if one too many, drop whichever end has the
    smaller `|E|` (the first, if equal), else drop the smallest `|E|` (the first, if equal) and
    merge again. It stops when the set does not change, or when the largest grid `|E|` is at
    most `|δ|·(1 + 1e-9) + 1e-12·S` (an optimum with more than `L + 1` equal
    extrema would otherwise swap between equally good sets). 250 iterations without stopping is
    `invalid_argument`: the design is beyond double precision. (This happens with ripples near
    rounding, and occasionally with many taps and wide gaps between bands, where the first set's
    `δ` can be below rounding and the exchange never leaves the noise; reference scaling makes
    that rarer, since the smaller design's set is already near the extrema.)
  - If every `desired` value is 0, or the kind is a filter, `N` is odd and all are equal, the taps
    are exact (`D·[n = (N−1)/2]`) and there is no iteration.
  - **Taps**: `c_0 … c_{L−1}` (and `δ` again) from the `(L+1)×(L+1)` linear system
    `Σ_k c_k cos(2πkν_i) + (−1)^i δ/W'_i = D'_i` at the final set, solved with partial pivoting.
    (Sampling `P` uniformly and inverting a DFT would read `P` in the gaps between bands, where
    interpolation from the band points magnifies rounding enormously.) The taps are then
    checked: the largest grid `|W'(D' − P)|` with these `c_k` must be at most
    `|δ|·(1 + 1e-3) + 1e-10·S`, else `invalid_argument` (beyond double precision).
    The excess is the rounding of `P`, about `ε·max W'·Σ|c_k|`; it fails when the ripple is near
    or below 1e-13, or when gaps between bands are so wide that the optimum needs huge
    coefficients (its response in the gaps then reaches 1e6 or more, and its taps are
    ill-determined although its band error is optimal). Near this limit the two languages may
    differ in whether a design raises, but anything returned meets the bound. Type I:
    `h[(N−1)/2] = c_0`, `h[(N−1)/2 ± k] = c_k/2`. Type II: `A = Σ_{k=1}^{L} β_k cos(2π(k − ½)ν)`
    with `β_1 = c_0 + c_1/2`, `β_k = (c_{k−1} + c_k)/2`, `β_L = c_{L−1}/2` (`β_1 = c_0` if
    `L = 1`), and `h[N/2 − 1 + k] = h[N/2 − k] = β_k/2`. Type III: `A = Σ_{m=1}^{L} a_m sin(2πmν)`
    with `a_1 = c_0 − c_2/2`, `a_m = (c_{m−1} − c_{m+1})/2` (`c_k = 0` for `k ≥ L`), and
    `h[c + m] = −h[c − m] = a_m/2`, `h[c] = 0`. Type IV: `A = Σ_{m=1}^{L} b_m sin(2π(m − ½)ν)` with
    `b_1 = c_0 − c_1/2`, `b_m = (c_{m−1} − c_m)/2` (`c_L = 0`), and
    `h[N/2 − 1 + m] = −h[N/2 − m] = b_m/2`.
- **Least-squares design** (`fir_least_squares(num_taps, bands, desired, sample_rate,
  weights=None)`, [ADR 0029](adr/0029-least-squares-fir.md)): the symmetric taps whose zero-phase
  gain `A` (as above) minimizes the weighted integral squared error
  `E = Σ_j W_j ∫_{band j} (A(ν) − D_j(ν))² dν` over normalized frequency `ν = f/fs`, **an exact
  integral, not a grid**.
  - Arguments: `bands` as for equiripple design (edge pairs in Hz, strictly increasing, from `≥ 0`
    to `≤ fs/2`); `desired` has **two values per band**, the gain at its lower and upper edge, and
    `D_j` is linear between them; `weights` one positive finite value per band (default all 1).
    `1 ≤ num_taps ≤ 1001`. Even `num_taps` is type II: `A(fs/2) = 0` whatever `desired` says
    there (it is only part of the error).
  - Basis: `A(ν) = Σ_{k<L} a_k cos(2π t_k ν)` with `t_k = k`, `L = (N + 1)/2` (odd `N`), or
    `t_k = k + ½`, `L = N/2` (even `N`). Taps: odd `N`, `h[c] = a_0` and
    `h[c + k] = h[c − k] = a_k/2` (`c = (N − 1)/2`); even `N`, `h[N/2 + k] = h[N/2 − 1 − k] = a_k/2`.
  - The normal equations `G·a = p`, `G_kl = Σ_j W_j ∫ cos(2π t_k ν) cos(2π t_l ν) dν`,
    `p_k = Σ_j W_j ∫ D_j(ν) cos(2π t_k ν) dν`, in closed form with
    `C(u) = ∫_α^β cos(2πuν) dν` (`= β − α` at `u = 0`, else
    `(sin 2πuβ − sin 2πuα)/(2πu)`) and `S(u) = ∫_α^β ν cos(2πuν) dν` (`= (β² − α²)/2` at `u = 0`,
    else `[ν sin(2πuν)/(2πu) + cos(2πuν)/(2πu)²]_α^β`): `G_kl = Σ_j W_j (C(t_k − t_l) +
    C(t_k + t_l))/2`, and with slope `s_j = (D_hi − D_lo)/(β − α)`,
    `p_k = Σ_j W_j ((D_lo − s_j α)·C(t_k) + s_j·S(t_k))`. `G` is symmetric positive definite (the
    cosines are independent on any interval); each language solves it in its own way, so taps
    agree to rounding times the condition of `G`.

  `H(f) = Σ h[n]·e^(−j2π·f·n/fs)` at each frequency (`n` from 0, so it includes the delay).
  Real taps, non-empty and finite; frequencies finite.
- **Group delay** (`fir_group_delay(taps, frequencies, sample_rate)`,
  [ADR 0028](adr/0028-group-delay.md)): `τ(f) = −dφ/dω` in **samples** (`ω = 2πf/fs`, `φ` the
  phase of `H`), so a pure delay of `d` samples gives `+d` and linear-phase taps give `(N − 1)/2`.
  It is computed in closed form, never by unwrapping a phase: for a polynomial
  `P(ω) = Σ c_n·e^(−jωn)` and `R(ω) = Σ n·c_n·e^(−jωn)`, `τ_P = Re(R/P)`. Where
  `|P| ≤ 1e-10·Σ|c_n|` (a zero on or within rounding of the unit circle, where the phase jumps)
  the result is NaN. Arguments as for `fir_response`.
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
    `b = [1, −2, 1]/D` (the code takes the gain from the computed `a`, `g = (1 ∓ a1 + a2)/4`,
    which equals these to rounding and gives exactly unit gain at the reference); the first-order low-pass is `b = K·[1, 1, 0]/(K + 1)`,
    `a = [1, (K − 1)/(K + 1), 0]`, the high-pass the same `a` with `b = [1, −1, 0]/(K + 1)`.
  - `order` is an integer, `1 ≤ order ≤ 1000`; `0 < cutoff < fs/2`, finite.
  - **Every IIR design** (Butterworth, Chebyshev, elliptic, band forms) checks its sections: each must be
    finite and strictly stable (`|a2| < 1`, `|a1| < 1 + a2`). A cutoff or band edge within about
    1e-8·fs of 0 or `fs/2` rounds a pole onto the unit circle (and the gain to 0), so such a
    design is `invalid_argument`; accuracy is already reduced near that limit (below about
    1e-6·fs). Band designs have the same limit for the bandwidth: poles sit about `high − low`
    from the unit circle, so a band narrower than about 1e-8·fs is `invalid_argument` or loses
    digits (a 1e-12·fs band matches the closed form only to about 1e-3), and extreme dB values
    (ripple near 200 dB, attenuation near 0; for elliptic, ripple above about 100 dB, where a
    pole can sit one rounding step from the circle) push poles closer still. Designs near these limits
    are not used as cross-language vectors: which side of the limit they land on depends on
    the last bit of `tan` and `sinh`. dB arguments enter as `10^(x/10) − 1`, computed as `expm1(x·ln10/10)` so small
    values keep their digits.
- **Chebyshev type I design** (`chebyshev1_lowpass(order, ripple_db, cutoff, sample_rate)` and
  `chebyshev1_highpass(...)`, [ADR 0018](adr/0018-chebyshev-type-1.md)): the analog Chebyshev
  type I filter with pass-band ripple `ripple_db` (`R`), through the same prewarped bilinear
  transform as Butterworth. With `ε = √(10^(R/10) − 1)`, `K = tan(π·f_c/fs)`, `t = tan(πf/fs)` and
  `T_N` the Chebyshev polynomial of degree `N = order` (`cos(N·acos x)` for `|x| ≤ 1`,
  `cosh(N·acosh x)` for `x > 1`, `T_N(−x) = (−1)^N·T_N(x)`):
  `|H(f)|² = 1/(1 + ε²·T_N(t/K)²)` for the low-pass and `1/(1 + ε²·T_N(K/t)²)` for the high-pass.
  So the pass band ripples between 1 and `1/(1 + ε²)` (−`R` dB), and the cutoff is the edge of
  the pass band, where `|H|²` is `1/(1 + ε²)`, not −3 dB.
  - Prototype poles (cutoff 1): with `μ = asinh(1/ε)/N` and `θ_k` as for Butterworth,
    `p_k = sinh μ·cos θ_k + j·cosh μ·sin θ_k`. The low-pass maps `p_k` to `K·p_k`, the high-pass to
    `K/p_k`, then through `z = (1 + s)/(1 − s)`.
  - Sections in the Butterworth order (the real pole `k = (order − 1)/2` first for an odd order,
    then pairs `k = ⌊order/2⌋ − 1` down to 0), with the same zeros, each with unit gain at DC
    (low-pass) or `fs/2` (high-pass). Then, for an even order only, the first section's `b` is
    multiplied by `10^(−R/20) = 1/√(1 + ε²)`: an even-order Chebyshev filter has its ripple's low
    point at DC (low-pass) or `fs/2` (high-pass). An odd order has gain 1 there.
  - `order` is an integer, `1 ≤ order ≤ 1000`; `0 < ripple_db ≤ 200`; `0 < cutoff < fs/2`, finite. Past
    200 dB the poles are within about 1e-11 of the unit circle and `10^(R/10)` soon overflows, so
    larger ripples are `invalid_argument`.
- **Chebyshev type II design** (`chebyshev2_lowpass(order, attenuation_db, cutoff, sample_rate)`
  and `chebyshev2_highpass(...)`, [ADR 0020](adr/0020-chebyshev-type-2.md)): the inverse
  Chebyshev filter, flat in the pass band and rippling in the stop band, whose peaks reach
  `−attenuation_db` (`A`). With `ε = 1/√(10^(A/10) − 1)` and `K`, `t`, `T_N` as for type I:
  `|H(f)|² = ε²·T_N(K/t)²/(1 + ε²·T_N(K/t)²)` for the low-pass and the same with `T_N(t/K)` for
  the high-pass. The cutoff is the **stop-band edge**, where `|H|²` first reaches `10^(−A/10)`.
  - Prototype (stop-band edge 1): with the type I poles `p_k` for this `ε` (`μ = asinh(1/ε)/N`),
    the poles are `1/p_k`; pair `k` has zeros at `s = ±j/sin θ_k`, and for an odd order the real
    pole's zero is at infinity. The low-pass scales `s` by `K`, the high-pass maps `s` to `K/s`,
    then `z = (1 + s)/(1 − s)`. So pair `k`'s zeros are on the unit circle at `z = (1 ± jw)/(1 ∓ jw)`
    with `w = K/sin θ_k` (low-pass) or `K·sin θ_k` (high-pass): `b ∝ [1, −2c, 1]`,
    `c = (1 − w²)/(1 + w²)`; the real pole's zero is at `z = −1` (low-pass) or `z = 1` (high-pass).
  - Sections in the Butterworth order, pair `k` with its own zeros, each with unit gain at DC
    (low-pass) or `fs/2` (high-pass); with no pass-band ripple there is no extra factor.
  - `order` is an integer, `1 ≤ order ≤ 1000`; `0 < attenuation_db ≤ 200`; `0 < cutoff < fs/2`, finite.
- **Elliptic (Cauer) design** (`elliptic_lowpass(order, ripple_db, attenuation_db, cutoff,
  sample_rate)` and `elliptic_highpass(...)`, [ADR 0022](adr/0022-elliptic.md)): equiripple in
  both bands, pass-band ripple `ripple_db` (`R`) and stop-band peaks at `−attenuation_db` (`A`).
  With `ε_p = √(10^(R/10) − 1)`, `ε_s = √(10^(A/10) − 1)` (both as `expm1`), `K`, `t` as for
  type I, and `x = t/K` (low-pass) or `K/t` (high-pass): `|H(f)|² = 1/(1 + ε_p²·R_N(x)²)`. Here
  `R_N` is the elliptic rational function of order `N` with `|R_N| ≤ 1` on `[0, 1]`, `R_N(1) = 1`,
  and `|R_N| ≥ ε_s/ε_p` from `1/k` on, each bound reached `N` times (and at `x = 1/k`). The
  cutoff is the **pass-band edge**, where `|H|²` last equals `10^(−R/10)`; the stop band starts at
  `x = 1/k`, so the low-pass stop-band edge is `fs/π·atan(K/k)`.
  - Moduli: `k₁ = ε_p/ε_s` (`k₁' = √((1 − k₁)(1 + k₁))`) and the selectivity `k` from the degree
    equation `K'(k)/K(k) = K'(k₁)/(N·K(k₁))`, written `τ`. `K` is the complete elliptic integral
    of the first kind, `K'(m) = K(m')`. With the nome `q = e^(−πτ)`: if `τ ≥ 1`,
    `k = 4√q·∏_{m≥1}((1 + q^(2m))/(1 + q^(2m−1)))⁴` and `k' = √((1 − k)(1 + k))`; else the same
    product of `q' = e^(−π/τ)` gives `k'`, and `k = √((1 − k')(1 + k'))`. Factors are taken while
    `q^(2m−1) > 1e-18`.
  - Landen ladder of a modulus `m` (with its complement `m'` given separately): `m_{j+1} =
    (m_j/(1 + m_j'))²`, `m'_{j+1} = 2√m_j'/(1 + m_j')`, while `m_j > 1e-12`. Then
    `K(m) = π/2·∏(1 + m_j)` over `j ≥ 1`, and `cd(uK, m)` (`u` real or complex) starts from
    `w = cos(uπ/2)` and runs `w ← (1 + m_j)·w/(1 + m_j·w²)` from the last `j` down to 1.
  - `v₀` (the imaginary offset): `y = 1/ε_p`, then for each `j ≥ 1` of `k₁`'s ladder
    `y ← 2y/((1 + k₁_j)(1 + √(1 + k₁_{j−1}²·y²)))`; `v₀ = 2/π·asinh(y)/N`. (This is
    `−j·sn⁻¹(j/ε_p, k₁)/N` normalized by `K₁`; for `k₁ → 0` it is type I's `μ`·2/π.)
  - Prototype (pass-band edge 1): pole `i`, for `0 ≤ i ≤ (N − 1)/2`, is
    `p_i = j·cd((u_i − j·v₀)K, k)` with `u_i = (2i + 1)/N`; for an odd order `i = (N − 1)/2`
    (`u = 1`) is the real pole, taken as the real part. Pair `i`'s zeros are at
    `s = ±j/(k·cd(u_iK, k))`; the real pole's zero is at infinity. Order 1 is the order-1 type I.
  - Low-pass and high-pass transform, sections, zero placement and gains exactly as for type II
    (pair `i` with its own zeros, unit gain at DC or `fs/2` per section, in the Butterworth order
    of `i`); an even order then multiplies the first section's `b` by `10^(−R/20)`, as type I.
  - `order` is an integer, `1 ≤ order ≤ 1000`; `0 < ripple_db < attenuation_db ≤ 200`;
    `0 < cutoff < fs/2`, finite. A design with `k' < 1e-6` is `invalid_argument`: its stop band
    would start within `1/k − 1 ≈ k'²/2 < 5e-13` of the cutoff (high order, or `A − R` small for
    the order), where the poles sit on the unit circle to rounding; one whose poles round
    onto the unit circle is too, as for every IIR design.
- **Bessel (Thomson) design** (`bessel_lowpass(order, cutoff, sample_rate)` and
  `bessel_highpass(...)`, [ADR 0025](adr/0025-bessel.md)): the analog Bessel filter, maximally
  flat group delay, through the same prewarped bilinear transform as Butterworth, normalized so
  that the **cutoff is the −3 dB point**: `|H|² = 1/2` exactly there, as for Butterworth.
  - With the reverse Bessel polynomial `θ_N(s) = Σ_{k=0}^{N} a_k s^k`,
    `a_k = (2N − k)!/(2^(N−k)·k!·(N − k)!)` (so `θ_1 = s + 1`, `θ_2 = s² + 3s + 3`, and
    `θ_N = (2N − 1)θ_{N−1} + s²θ_{N−2}`), the prototype is `H(s) = θ_N(0)/θ_N(ω₀·s)`, where `ω₀ > 0`
    solves `|θ_N(jω₀)|² = 2·θ_N(0)²` (`|θ_N(jω)|²` is a polynomial in `ω²` with positive
    coefficients, so the root is unique). Its poles are `p/ω₀` for the roots `p` of `θ_N`.
    Then `|H(f)|² = θ_N(0)²/|θ_N(jω₀·t/K)|²` for the low-pass and the same with `K/t` for the
    high-pass (`K = tan(π·f_c/fs)`, `t = tan(πf/fs)`).
  - Sections in the Butterworth order: the real pole first for an odd order, then the pairs from
    the lowest Q to the highest (pair 0 is the root with the largest `Im p/|Re p|`), with the
    Butterworth zeros (at `z = −1` for the low-pass, `z = 1` for the high-pass) and unit gain at
    DC (low-pass) or `fs/2` (high-pass). The roots are found to double precision by any method
    (this code: Aberth's iteration, evaluating `θ_N` and `θ_N'` by the recurrence, then a
    Newton step); `ω₀` likewise (this code: bisection).
  - `order` is an integer, `1 ≤ order ≤ 10`; `0 < cutoff < fs/2`, finite. The roots of `θ_N` are
    sensitive to rounding: in double they hold about 1e-12 relative at order 10, 1e-9 at 15 and
    1e-4 at 25, so higher orders are `invalid_argument`.
  - The bilinear transform keeps the magnitude's shape (warped in frequency) but not the flat
    group delay: the digital filter's delay is flat only while the cutoff is well below `fs/2`.
- **Band-pass and band-stop Butterworth** (`butterworth_bandpass(order, low, high, sample_rate)`,
  `butterworth_bandstop(...)`, [ADR 0016](adr/0016-band-butterworth.md)): the low-pass prototype
  of that `order` (cutoff 1, poles `p_k = e^(jθ_k)` as above) transformed to the band, through the
  bilinear transform `s = (1 − z⁻¹)/(1 + z⁻¹)` (the factor `2·fs` cancels against the prewarping).
  With `L = tan(π·low/fs)`, `H = tan(π·high/fs)`, `W² = L·H` and `B = H − L`, and
  `t = tan(π·f/fs)`, `x = (t² − W²)/(B·t)`:
  `|H(f)|² = 1/(1 + x^(2·order))` for the band-pass and `x^(2·order)/(1 + x^(2·order))` for the
  band-stop, so exactly `1/2` at `low` and `high`, and `1` (band-pass) or `0` (band-stop) at the
  center `f_0 = (fs/π)·atan(W)`. The design has `order` sections, filter order `2·order`:
  - each section is the analog `B·s/(s² − 2σs + m)` (band-pass) or `(s² + W²)/(s² − 2σs + m)`
    (band-stop) for one pole `s` of the band filter and its conjugate, `σ = Re s`, `m = |s|²`;
    through the bilinear transform, with `a0 = 1 − 2σ + m`,
    `a = [1, 2(m − 1)/a0, (1 + 2σ + m)/a0]` and `b = B·[1, 0, −1]/a0` (band-pass) or
    `b = [1 + W², 2(W² − 1), 1 + W²]/a0` (band-stop). The cascade's gain is then that of
    the formula above, to rounding (see ADR 0016 for poles very near `z = 1`); a single
    section's gain is whatever its own formula gives.
  - for an odd `order`, first the section from the real prototype pole `−1`: `σ = −B/2`, `m = W²`
    (the quadratic `s² + B·s + W²`, whether its roots are complex or real);
  - then, for `k = ⌊order/2⌋ − 1` down to 0, two sections from the prototype pole `p_k`: its two
    images, the roots `s = (c ± √(c² − 4W²))/2` of `s² − c·s + W²`, with `c = B·p_k` (band-pass) or
    `c = B/p_k` (band-stop), the root with the smaller `|s|` first.
  - `order` is an integer, `1 ≤ order ≤ 1000`; `0 < low < high < fs/2`, finite.
- **Band-pass and band-stop Chebyshev** (`chebyshev1_bandpass(order, ripple_db, low, high,
  sample_rate)`, `chebyshev1_bandstop(...)`, `chebyshev2_bandpass(order, attenuation_db, low, high,
  sample_rate)`, `chebyshev2_bandstop(...)`, [ADR 0021](adr/0021-band-chebyshev.md)): the type I
  or type II low-pass prototype of that `order` (edge 1; poles `p_k`, zeros `±jΩ_k`,
  `Ω_k = 1/sin θ_k` for type II, as above) through the band transform and bilinear transform of
  the band Butterworth, with the same `L, H, W, B, t` and `x = (t² − W²)/(B·t)` (band-pass) or
  `x = B·t/(W² − t²)` (band-stop): the band filter's `|H(f)|²` is the low-pass prototype's at
  frequency `|x|`, so for type I `1/(1 + ε²T_N²(x))`, and for type II
  `ε²T_N²(1/x)/(1 + ε²T_N²(1/x))`. `low` and `high` are where `|x| = 1`: the pass-band edges
  (type I, `|H|² = 1/(1 + ε²)`) or the stop-band edges (type II, `|H|² = 10^(−A/10)`); a type II
  band-pass passes the band inside them and a type II band-stop stops the band inside them.
  Sections, in the band Butterworth's order:
  - the odd `order`'s real prototype pole `p_r` (`−sinh μ`, type I; `−1/sinh μ`, type II) gives
    one section with the quadratic `s² − c·s + W²`, `c = B·p_r` (band-pass) or `B/p_r`
    (band-stop): `σ = c/2`, `m = W²`;
  - pair `k`'s two images as for Butterworth (`c = B·p_k` or `B/p_k`, smaller `|s|` first);
  - numerators: band-pass `B·s` and band-stop `s² + W²`, as for Butterworth, except that type II
    pair sections have `s² + ω²`, a zero pair on the unit circle (bilinear:
    `b ∝ [1 + ω², 2(ω² − 1), 1 + ω²]/a0`). The prototype zero `jΩ_k` maps to `jω_hi` and `jω_lo`,
    `ω_hi = (d + √(d² + 4W²))/2`, `ω_lo = W²/ω_hi`, with `d = B·Ω_k` (band-pass) or `B/Ω_k`
    (band-stop); the smaller-`|s|` section takes `ω_lo`, the other `ω_hi`;
  - gains, from the prototype's own factors so the cascade equals it exactly: band-pass, the
    real-pole section `× (−p_r)`, each pair section `× |p_k|` (type I) or `× |p_k|/Ω_k`
    (type II); band-stop, every section `× 1`. Type I of even `order` multiplies the first
    section's `b` by `10^(−R/20)`, as for the low-pass. So the band-pass has the prototype's DC
    gain at the center `f_0`, and the band-stop has it at 0 and `fs/2`.
  - `order` is an integer, `1 ≤ order ≤ 1000`; `ripple_db` or `attenuation_db` in `(0, 200]`;
    `0 < low < high < fs/2`, finite.
- **Band-pass and band-stop elliptic** (`elliptic_bandpass(order, ripple_db, attenuation_db, low,
  high, sample_rate)`, `elliptic_bandstop(...)`, [ADR 0023](adr/0023-band-elliptic.md)): the
  elliptic low-pass prototype of that `order` (edge 1; poles `p_i`, zeros `±jΩ_i`,
  `Ω_i = 1/(k·cd(u_i K, k))`, as above, with the same validation and `k' ≥ 1e-6` limit) through
  the band transform exactly as the band Chebyshev, with the same `L, H, W, B, t, x`:
  `|H(f)|² = 1/(1 + ε_p²R_N(|x|)²)`. `low` and `high` are the pass-band edges (`|x| = 1`,
  `|H|² = 1/(1 + ε_p²)`); the stop band is `|x| ≥ 1/k`. Sections as for the band Chebyshev:
  the odd order's real pole `p_r` as type I (band-pass gain `−p_r`), each pair with its zeros as
  type II (`d = B·Ω_i` or `B/Ω_i`, the smaller-`|s|` image takes `ω_lo`; band-pass gain
  `|p_i|/Ω_i`), band-stop gains 1; an even `order` multiplies the first section's `b` by
  `10^(−R/20)`. So the band-pass has the prototype's DC gain (`1`, or `10^(−R/20)` for an even
  order) at the center `f_0`, and the band-stop has it at 0 and `fs/2`; the band-stop's center
  maps to `|x| = ∞`, where `|H|²` is 0 (odd order) or `10^(−A/10)` (even).
- **Band-pass and band-stop Bessel** (`bessel_bandpass(order, low, high, sample_rate)`,
  `bessel_bandstop(...)`, [ADR 0032](adr/0032-band-bessel.md)): the Bessel low-pass prototype of
  that `order` (poles `p/ω₀`, −3 dB at 1, as in Bessel design; `1 ≤ order ≤ 10`) through the band
  transform exactly as the band Chebyshev type I, with the same `L, H, W, B, t, x`:
  `|H(f)|² = θ_N(0)²/|θ_N(jω₀·x)|²`. So `low` and `high` are the −3 dB points (`|H|² = 1/2`); the
  band-pass has gain 1 at the center `f_0`, and the band-stop gain 1 at 0 and `fs/2` and 0 at
  `f_0`. Sections as for the band Chebyshev type I: the odd order's real pole `p_r` first
  (`c = B·p_r` or `B/p_r`, `σ = c/2`, `m = W²`; band-pass gain `−p_r`), then the pairs from the
  lowest Q to the highest, each pole's two images with the smaller `|s|` first, numerators `B·s`
  (band-pass) or `s² + W²` (band-stop), band-pass pair gains `|p_k|`, band-stop gains 1. Order 1
  is the order-1 band Butterworth. The delay is flat in the prototype's frequency `x`, not in
  `f`: the band transform does not keep the Bessel's flat group delay.
- **All-pass sections** (`allpass_first_order(cutoff, sample_rate)`,
  `allpass_second_order(center, bandwidth, sample_rate)`, [ADR 0033](adr/0033-allpass.md)): one
  section each, `|H| = 1` at every frequency, for phase equalization. With `t = tan(π·f/fs)` of
  the frequency named and `c = (t − 1)/(t + 1)`:
  - first order, `t` of the `cutoff`: `[c, 1, 0, 1, c, 0]`, the bilinear transform of
    `(K − s)/(K + s)`. The phase falls from 0 at DC through `−π/2` at the cutoff (`H = −j`) to
    `−π` at `fs/2` (`H = −1`).
  - second order, `t` of the `bandwidth` and `d = −cos(2π·center/fs)`:
    `[−c, d(1 − c), 1, 1, d(1 − c), −c]`. The phase falls from 0 at DC through `−π` at the
    center (`H = −1`) to `−2π` at `fs/2`; it is `−π/2` (`H = −j`) at `f₁` and `−3π/2`
    (`H = j`) at `f₂`, with `f₂ − f₁ = bandwidth` exactly and
    `cos(π(f₁ + f₂)/fs) = cos(2π·center/fs)·cos(π·bandwidth/fs)`, both inside `(0, fs/2)`.
  - `cutoff`, `center` and `bandwidth` each strictly between 0 and `fs/2`, finite; a design whose
    pole rounds onto the unit circle is `invalid_argument`, as for every IIR design.
- **Frequency response** (`sos_response(sos, frequencies, sample_rate)`): the complex
  `H(f) = Π_i H_i(e^(j2π·f/fs))` at each frequency. Frequencies finite.
- **Group delay** (`sos_group_delay(sos, frequencies, sample_rate)`,
  [ADR 0028](adr/0028-group-delay.md)): the sum over sections of `τ_B − τ_A`, each by the FIR
  rule (FIR filters, Group delay) for `B = b0 + b1·e^(−jω) + b2·e^(−j2ω)` and `A` likewise, after
  dividing by `a0`. NaN where any section's `B` or `A` meets the NaN rule. Arguments as for
  `sos_response`.
- **Streaming filter** (`IirFilter(sos)`, method `process(chunk)`, `reset()`, property `sections`,
  a copy with `a0 = 1`): each section is the causal difference equation
  `y[n] = b0·x[n] + b1·x[n−1] + b2·x[n−2] − a1·y[n−1] − a2·y[n−2]` (after dividing by `a0`), with
  zero initial state, the sections in cascade, over the concatenation of every chunk since the start
  or the last reset. How each language arranges the arithmetic (direct form I, transposed direct
  form II) is its own; results agree to rounding. Otherwise as `FirFilter`: each call returns as
  many samples as it is given, the first non-empty chunk fixes the filter as real or complex until
  `reset()`, and an empty chunk changes nothing.
- **Zero-phase filtering** (`zero_phase_filter(sos, samples, pad=None)`,
  [ADR 0017](adr/0017-zero-phase-filtering.md)): with `P = pad` (default `3·(2·sections + 1)`)
  and `N` samples, `N > P`:
  1. extend by odd reflection about the end samples: `x[−i] = 2·x[0] − x[i]` and
     `x[N−1+i] = 2·x[N−1] − x[N−1−i]` for `i = 1 … P`;
  2. run the cascade over the extended samples, each section starting in its steady state for a
     constant input `u` (past inputs `u`, past outputs `g·u`, `g = (b0 + b1 + b2)/(1 + a1 + a2)`),
     with `u` the first extended sample for the first section and `g·u` of the previous section
     for each later one;
  3. reverse, run again the same way, reverse back, and keep the middle `N` samples.
  The result has as many samples as the input and its kind (real or complex); in steady state it
  is the input with every frequency scaled by `|H(f)|²` and no delay. Every section needs
  `1 + a1 + a2 ≠ 0` (no pole at `z = 1`, after dividing by `a0`); `pad` is an integer `≥ 0`;
  samples must be finite (one non-finite sample would spoil every output). Near `1 + a1 + a2 = 0`
  the steady state `g` is huge; that is what the coefficients say, and it is not guarded.

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
- **Streaming resampling** (`Resampler(up, down, taps=None)`, methods `process(chunk)` and
  `reset()`, [ADR 0027](adr/0027-streaming-resampling.md)): causal. With `L, M` reduced as above,
  `u` the zero-stuffed concatenation of every chunk since the start or the last reset (zero
  before its first sample) and taps `h` of length `N`, the output stream is
  `z[m] = L·Σₖ h[k]·u[m·M − k]`, `m = 0, 1, …`. After `n` input samples in all, exactly
  `⌈n·L/M⌉` outputs have been returned: output `m` comes out with the chunk that holds its last
  input, sample `⌊m·M/L⌋`. So the outputs of any split concatenate to the same stream, which is
  `resample(x, up, down, [0]·(N − 1) + h)` (the taps delayed by `N − 1` at the up-sampled rate);
  for symmetric taps, output `m` is at input time `(m·M − (N − 1)/2)/L`. Taps are real,
  non-empty and finite, of any length; the default is `resample_taps(up, down)`, or `[1]` when
  `L = M = 1` (a copy). The first non-empty chunk fixes the stream as real or complex; a chunk of
  the other kind raises, until `reset()`. An empty chunk returns an empty output and changes
  nothing.

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
- **IQ imbalance** (`iq_imbalance(samples, gain_db, phase)`, [ADR 0034](adr/0034-iq-impairments.md)):
  the error is on the Q branch. With `g = 10^(gain_db/20)` and `φ` in radians,
  `y = I + j·g·(Q·cos φ + I·sin φ)`: for `x = e^{jθ}` the output is `cos θ + j·g·sin(θ + φ)`,
  so a positive `φ` advances the Q branch. Equivalently `y = μ·x + ν·x̄` with
  `μ = (1 + g·e^{jφ})/2`, `ν = (1 − g·e^{−jφ})/2`: a tone at `+f` gets an image at `−f`. `gain_db`
  and `φ` finite, `g` finite. **(implemented)**
- **Image rejection** (`iq_image_rejection_db(gain_db, phase)`): `10·log10(|μ|²/|ν|²) =
  10·log10((1 + g² + 2g·cos φ)/(1 + g² − 2g·cos φ))`, the tone-to-image power ratio of that
  imbalance; `+inf` with no imbalance (`g = 1`, `φ = 0`). **(implemented)**
- **Phase noise** (`phase_noise(samples, linewidth_hz, sample_rate, *, seed)`,
  [ADR 0036](adr/0036-phase-noise.md)): Wiener (random-walk) phase, `y[n] = x[n]·e^{jφ[n]}` with
  `φ[0] = 0` and `φ[n] = φ[n−1] + Δ[n]`, the `Δ[n]` independent Gaussian of mean 0 and variance
  `σ² = 2π·linewidth_hz/sample_rate`. That is the oscillator whose spectrum is a Lorentzian of
  full 3 dB width `linewidth_hz`; `E[e^{jφ[n]}] = e^{−nσ²/2}`. `linewidth_hz` finite and `≥ 0`
  (0 is the identity); seeded as for AWGN, with streams that differ between languages.
  **(implemented)**
- **DC offset** (`dc_offset(samples, offset)`): `y = x + offset`, `offset` a complex number (a real
  one is `offset + 0j`), finite in both parts. **(implemented)**
- **Multipath** (`multipath(samples, delays, gains)`, [ADR 0038](adr/0038-multipath.md)): a static
  tapped delay line, `y[n] = Σᵢ gains[i]·x[n − delays[i]]` with `x[m] = 0` for `m < 0`, for
  `n = 0 … N−1`: the output is as long as the input and the tail past the last sample is dropped
  (as a receiver that keeps sampling the same window sees it). `delays` are integers `≥ 0` in
  samples, `gains` complex and finite, the two of equal non-zero length; a repeated delay adds its
  gains, and a delay `≥ N` contributes nothing. Paths are summed in the order given.
  **(implemented)**
- **Fractional delay** (`fractional_delay(samples, delay, *, half_width=16)`,
  [ADR 0040](adr/0040-fractional-delay.md)): `y[n] = Σ_m x[m]·h(n − delay − m)` for
  `n = 0 … N−1`, `x[m] = 0` outside `0 … N−1`, with the Kaiser-windowed sinc
  `h(t) = sinc(t)·I₀(β·√(1 − (t/H)²))/I₀(β)` for `|t| < H` and 0 otherwise, `β = 8`,
  `H = half_width`, `sinc(t) = sin(πt)/(πt)`, `sinc(0) = 1`. With `p = n − delay`,
  `b = ⌊p⌋` and `f = p − b`, the sum runs over `m = b + j` for `j = −H+1 … H` in that order, so
  `t = f − j`; where `f = 0` the sinc is exactly 0 at every `t ≠ 0`, so an integer delay is an
  exact shift. `delay` is any finite real (negative advances), `half_width` an integer `≥ 1`.
  Output as long as the input, complex. A multipath channel with fractional delays is the sum of
  `gainᵢ·fractional_delay(x, delayᵢ)`. **(implemented)**
- **Block fading** (`rician_fading(samples, k_factor, block_length, *, seed)`,
  [ADR 0041](adr/0041-block-fading.md)): flat fading, one complex gain per block,
  `y[n] = g[⌊n/L⌋]·x[n]` with `L = block_length` (the last block may be short). Each gain is
  `g = √(K/(K+1)) + √(1/(K+1))·(a + jb)/√2`, `K = k_factor`, with `a` and `b` independent
  standard Gaussians drawn block by block, `a` first. So `E|g|² = 1`, `E[g] = √(K/(K+1))`, and
  `|g|` is Rician; `K = 0` is Rayleigh (`|g|²` exponential of mean 1). `K = ∞` is allowed and
  gives `g = 1` exactly (no draws are used). `k_factor` is `≥ 0` (not NaN), `block_length` an
  integer `≥ 1`; seeded as for AWGN, with streams that differ between languages. **(implemented)**
- **Sample clock offset** (`clock_offset(samples, ppm, *, half_width=16)`,
  [ADR 0045](adr/0045-clock-offset.md)): the input read every `r = 1 + ppm/1e6` samples,
  `y[n] = z(n·r)` with `n·r` computed as written, for every `n ≥ 0` with `n·r ≤ N − 1` (none for
  empty input), where `z(t)` reads between samples by the Fractional delay kernel exactly as
  in Tracking loops (`z(t) = Σ_j x[b+j]·h(f−j)`, `b = ⌊t⌋`, `f = t − b`, `j = −H+1 … H` in
  order, `x` zero outside `0 … N−1`). Positive `ppm` means the receiver's clock is slow: its
  samples are further apart, so a signal of `sps` samples per symbol comes out at `sps/r`.
  `ppm` finite with `|ppm| ≤ 1e5`; `half_width` an integer `≥ 1`. `ppm = 0` returns the input.
  **(implemented)**

## Synchronization

Decided in [ADR 0008](adr/0008-block-synchronization.md). Python: `signalforge.sync`; C#:
`SignalForge.Sync`. All but the tracking loops are block estimators over finite complex
samples; they estimate, they do not correct. Where a sum below is exactly zero there is no information and the estimate is 0. `arg`
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
- **Power-spectrum frequency offset** (`power_frequency_offset(symbols, symbol_rate, power)`,
  [ADR 0049](adr/0049-power-frequency-offset.md)): the frequency of the strongest line in the
  spectrum of `w = zᵖ`, divided by `p`. For any constellation whose `p`-th power has a non-zero
  mean (QPSK and 16-QAM at `p = 4`, 8-PSK at `p = 8`) it adds up the line over the whole block,
  so unlike the lag-1 estimator it is not swamped by 16-QAM's self-noise. `p = power` is an
  integer in `1 … 16`; at least two symbols; `symbol_rate` positive and finite. After the exact
  scaling above, `w[k]` is `z[k]` multiplied by `z[k]` `p − 1` times, left to right.
  1. `L` is the smallest power of two `≥ 4N` (`N` symbols). `P[i] = |W[i]|²`, `W` the `L`-point
     DFT of `w` zero-padded to `L`. If every `P[i]` is 0 the result is 0. Otherwise `i` is the
     first index of the largest `P[i]`, then `i − L` if `i > L/2`.
  2. With `S(ν) = Σₖ w[k]·e^{−j2πνk}` and `T(ν) = Σₖ k·w[k]·e^{−j2πνk}` (the angle computed as
     `(−2π·ν)·k`), `D(ν) = S.re·T.im − S.im·T.re` is `dA/dν / (4π)` for `A = |S|²`: positive
     below a peak, negative above. Starting from `lo = (i − 1)/L`, `hi = (i + 1)/L`, 60 times:
     `m = (lo + hi)/2`; if `D(m) > 0` then `lo = m`, else `hi = m`. Then `ν = (lo + hi)/2`,
     moved by 1 into `(−1/2, 1/2]` if outside.
  3. `Δf = ν·symbol_rate/p`, in `(−Rs/(2p), Rs/(2p)]`.

  For `z[k] = A·e^{j(2πfk/Rs + φ)}` times constellation points whose `p`-th powers are all the
  same, `w` is a single tone and the estimate is `f` (wrapped into the range) to rounding. The
  grid spacing `1/L ≤ 1/(4N)` is a quarter of the main lobe's half-width, so the largest bin is
  within `1/L` of the true peak and `D` changes sign once in `[lo, hi]`. **(implemented)**
- **Tracking loops** ([ADR 0043](adr/0043-gardner-timing.md),
  [ADR 0044](adr/0044-qpsk-carrier-loop.md)). These take the samples as given (no scaling).
  - `pi_loop_gains(loop_bandwidth, damping, detector_gain)` returns `(kp, ki)` for a
    proportional-plus-integral loop whose detector has slope `Kd = detector_gain`, with
    `Bn = loop_bandwidth` the one-sided noise bandwidth per update and `ζ = damping`:
    `θ = Bn/(ζ + 1/(4ζ))`, `d = 1 + 2ζθ + θ²`, `kp = 4ζθ/d/Kd`, `ki = 4θ²/d/Kd`, evaluated
    left to right as written. `0 < Bn < 0.5`, `ζ > 0`, `Kd > 0`, all finite.
  - `gardner_timing(samples, samples_per_symbol, kp, ki, *, start=0.0, half_width=8)`: the
    samples `y` (matched-filter output, finite, `sps = samples_per_symbol ≥ 2`) are read between
    samples by the fractional-delay kernel, `z(t) = Σ_j y[b+j]·h(f−j)` with `b = ⌊t⌋`,
    `f = t − b`, `j = −H+1 … H` in order, `h` as in Fractional delay with `H = half_width`, and
    `y` zero outside `0 … N−1` (so `z(n − d)` is `fractional_delay(y, d)[n]`). With `τ₀ = start`
    and `v = 0`, for `k = 0, 1, …` while `τₖ ≤ N − 1`: the symbol is `zₖ = z(τₖ)`; the
    detector is `eₖ = 0` for `k = 0` and otherwise `eₖ = Re{conj(m)·(zₖ − zₖ₋₁)}` computed as
    `m.re·Δ.re + m.im·Δ.im`, `m = z((τₖ₋₁ + τₖ)/2)`, `Δ = zₖ − zₖ₋₁` (positive when sampling
    late); then `v ← v + ki·eₖ`, `s = sps − kp·eₖ − v`, held to `[sps/2, 3·sps/2]`, and
    `τₖ₊₁ = τₖ + s`. The result has `symbols` (`zₖ`), `positions` (`τₖ`) and `errors` (`eₖ`),
    one each per symbol, empty if `start > N − 1`. `kp`, `ki` finite and `≥ 0`, `start` finite
    and `≥ 0`, `half_width` an integer `≥ 1`. In the linear model (`e = Kd·(τ − t)`) a clock
    whose symbols arrive every `sps·(1 + δ)` samples leaves a lag of `−sps·δ/(kp·Kd)` with
    `ki = 0`, and none with `ki > 0`. **(implemented)**
  - `qpsk_carrier_tracking(symbols, kp, ki, *, phase=0.0)`: a decision-directed phase-locked loop
    on QPSK symbols `z` (finite, the constellation at odd multiples of π/4). With `φ₀ = phase` and
    `v = 0`, for each `k`: `c = cos φₖ`, `s = sin φₖ`, the corrected symbol `rₖ = zₖ·e^(−jφₖ)`
    computed as `r.re = z.re·c + z.im·s`, `r.im = z.im·c − z.re·s`; the decision
    `d = sgn(r.re) + j·sgn(r.im)` with `sgn(x) = +1` for `x ≥ 0`, else `−1`; the detector
    `eₖ = d.re·r.im − d.im·r.re` (positive when the carrier is ahead of `φₖ`); then
    `v ← v + ki·eₖ` and `φₖ₊₁ = φₖ + kp·eₖ + v`, not wrapped. The result has `symbols` (`rₖ`),
    `phases` (`φₖ`) and `errors` (`eₖ`), one each per symbol. `kp`, `ki` finite and `≥ 0`,
    `phase` finite. Near lock the detector's slope is `Kd = √2·|z|`. For noise-free symbols of
    magnitude `A` it is exactly `√2·A·sin(θ − φ)`, so a carrier advancing `ω` per symbol leaves
    `θ − φ = asin(ω/(√2·A·kp))` with `ki = 0` (if that is below π/4), and none with `ki > 0`.
    The loop locks to the nearest multiple of π/2 to its start; resolving that is the
    caller's. **(implemented)**
  - `psk8_carrier_tracking` and `qam16_carrier_tracking` (same arguments and result,
    [ADR 0048](adr/0048-psk8-qam16-carrier-loops.md)): the same recurrence with another
    decision `d`, the detector still `eₖ = d.re·r.im − d.im·r.re`. 8-PSK: `p = ⌊atan2(r.im,
    r.re)/(π/4) + 1/2⌋ mod 8` as in the hard demapper, and `d` from the table
    `(1, 0), (c, c), (0, 1), (−c, c), (−1, 0), (−c, −c), (0, −1), (c, −c)` at `p`, with
    `c = 1/√2` (not `cos(π/4)`, so both languages use the same number). Its slope is `Kd = |z|`,
    exactly `|z|·sin(θ − φ)` noise-free, so the proportional lag is `asin(ω/(A·kp))` (below
    π/8); it locks to a multiple of π/4. 16-QAM: each part of `r` decided as in the hard
    demapper, level `±1` when `|v| < 2/√10` (`v ≥ 0` positive, so 0 decides `+1`), else `±3`,
    and `d = level/√10` per part (`1/√10` computed once, as in `qam16_map`). For a point `s`
    scaled by `A` the detector is `A·|s|²·sin(θ − φ)`, so the mean slope over the constellation
    is `A`; it locks to a multiple of π/2. **(implemented)**
  - `qam64_carrier_tracking` ([ADR 0053](adr/0053-qam64-link.md)): the same, each part of `r`
    decided as in `qam64_demap_hard` (so the ties go the same way: magnitude
    `4 + (1 − 2·[a < T₄])·(3 − 2·[T₂ < a < T₆])` with `a = |v|`, negative when `v < 0`), times
    `1/√42` (computed once, as in `qam64_map`). Mean slope `A`, locks to a multiple of π/2.
    **(implemented)**
- **QPSK phase offset** (`qpsk_phase_offset(symbols)`): `φ = arg(−Σ z⁴) / 4`, in `(−π/4, π/4]`;
  the true phase is `φ + m·π/2`. Correct by multiplying by `e^{−jφ}`
  (`frequency_offset(symbols, 0, 1, −φ)`). At least one symbol. **(implemented)**
- **QPSK block phases** (`qpsk_block_phases(symbols, block_symbols)`): block `b` holds symbols
  `b·B … min((b+1)·B, N) − 1` (the last block may be shorter), and `θ_b` is its
  `qpsk_phase_offset`. Unwrapped: `φ₀ = θ₀`, and `φ_b = θ_b + (π/2)·round((φ_{b−1} − θ_b)/(π/2))`,
  rounding half to even. Returns one value per block. `block_symbols ≥ 1`, at least one symbol.
  On `z_k = a_k·e^{j(θ + ωk)}` each block gives the phase at its middle, `θ + ω·(first + last)/2`,
  as long as consecutive blocks differ by less than π/4. **(implemented)**
- **8-PSK phase offset and block phases** (`psk8_phase_offset(symbols)`,
  `psk8_block_phases(symbols, block_symbols)`, [ADR 0051](adr/0051-psk8-link.md)): the same with
  the eighth power. 8-PSK points are at multiples of π/4, so `z⁸` of each is 1: `φ = arg(Σ z⁸)/8`
  in `(−π/8, π/8]`, `z⁸` computed as `((z²)²)²` after the exact scaling above; the true phase is
  `φ + m·π/4`. The block phases unwrap in steps of π/4:
  `φ_b = θ_b + (π/4)·round((φ_{b−1} − θ_b)/(π/4))`, half to even; each block gives the phase at
  its middle as long as consecutive blocks differ by less than π/8. **(implemented)**

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
- **16-QAM and 8-PSK error rates** ([ADR 0037](adr/0037-error-rate-theory.md)): Gray mapping as
  in Bits and symbols, AWGN, hard decisions, Eb/N0 in dB taken as for QPSK (NaN rejected, `−∞`
  gives the fair-guess rates, overflow is infinite and gives 0). `Es = k·Eb` with `k = 4` and 3.
  - `qam16_ber_theory`: with `r = √(2·Eb/N0/5)`,
    `Pb = (3·erfc(r) + 2·erfc(3r) − erfc(5r)) / 8`, exact for the Gray 4-PAM axes (a bit decided
    wrongly two thresholds away counts once).
  - `qam16_ser_theory`: `p = ¾·erfc(r)` per axis, `Ps = 1 − (1 − p)² = p·(2 − p)`.
  - `qam64_ber_theory` ([ADR 0052](adr/0052-qam64.md)): `k = 6`, `r = √(Eb/N0 / 7)` (half the
    spacing `1/√42` over `√N0`),
    `Pb = (7·erfc(r) + 6·erfc(3r) − erfc(5r) + erfc(9r) − erfc(13r)) / 24`, exact for the Gray
    8-PAM axes: the square-QAM bit error sum of Cho and Yoon (IEEE Trans. Commun. 50(7), 2002)
    for `√M = 8`, written out; the same sum for `√M = 4` gives the 16-QAM form above.
  - `qam64_ser_theory`: `p = ⅞·erfc(r)` per axis, `Ps = p·(2 − p)`.
  - `psk8_ser_theory`: `Ps = 2·T(π/8)`, and `psk8_ber_theory`: `Pb = ⅔·(T(π/8) + T(3π/8))`,
    exact for this Gray labeling (the mean bit distance is 1 to the next sector and 2 to each
    one further). `T(ψ)` is the probability that the received phase lies beyond `ψ` on one side,
    in Pawula's form `T(ψ) = (1/2π)·∫₀^{π−ψ} exp(−(Es/N0)·sin²ψ / sin²θ) dθ`, evaluated by
    Simpson's rule on 4096 panels (relative error below 1e-12 against the phase density's
    integral); `T(ψ) = (π − ψ)/2π` at `Es/N0 = 0` and 0 at infinity. **(implemented)**
- **Noncoherent orthogonal FSK** (`fsk_ser_theory(eb_n0_db, order=2)`,
  `fsk_ber_theory(eb_n0_db, order=2)`, [ADR 0054](adr/0054-fsk.md)): `M = order` in 2, 4, 8, 16,
  `Es/N0 = log2(M)·Eb/N0` (Eb/N0 from dB as for QPSK: NaN rejected, `−∞` gives the fair-guess
  rates, overflow is infinite and gives 0), the square-law detector of `fsk_demod_noncoherent`
  with orthogonal tones in AWGN.
  `Ps = Σ_{k=1}^{M−1} (−1)^{k+1}·C(M−1, k)/(k + 1)·e^{−k·(Es/N0)/(k+1)}`, summed from `k = 1` up,
  each term `C(M−1, k)/(k + 1)·exp(−k·g/(k + 1))` with `g = Es/N0` (Proakis, *Digital
  Communications*, noncoherent orthogonal signals), so for `M = 2`, `Ps = Pb = ½·e^{−Eb/(2N0)}`.
  Every wrong label is equally likely, so `Pb = Ps·(M/2)/(M − 1)`. At `Eb/N0 = 0`, `Ps = 1 − 1/M`
  and `Pb = ½` (within rounding of the sum). **(implemented)**
- **QPSK in Rayleigh fading** (`qpsk_ber_rayleigh_theory(eb_n0_db)`,
  [ADR 0042](adr/0042-rayleigh-ber.md)): the AWGN curve averaged over a Rayleigh gain with
  `E|g|² = 1` and a coherent receiver that knows `g`, with `γ` the mean Eb/N0 (linear, taken from
  dB as for QPSK): `Pb = ½·(1 − √(γ/(1+γ)))`, computed without cancellation as
  `Pb = 1 / (2·(1+γ)·(1 + √(γ/(1+γ))))`. `−∞` dB gives ½, an infinite `γ` gives 0, NaN is
  rejected. At high `γ`, `Pb ≈ 1/(4γ)`. **(implemented)**

## QPSK link

Decided in [ADR 0009](adr/0009-qpsk-link-report.md). Python: `signalforge.link`; C#:
`SignalForge.Link`. `qpsk_link(config)` runs one block and returns `QpskLinkReport`.

- **Config** (`QpskLinkConfig`, defaults in brackets): `num_symbols` (≥ 2), `eb_n0_db` [none: no
  noise], `symbol_rate` [1000] Hz, `samples_per_symbol` [4] (≥ 2), `rolloff` [0.35],
  `span_symbols` [10], `delay_samples` [0], `frequency_offset_hz` [0], `phase` [0] rad,
  `preamble_symbols` [32] (1 to `num_symbols`), `phase_block_symbols` [32] (≥ 1; 64-QAM wants 64 or more, [ADR 0053](adr/0053-qam64-link.md)), `prbs_order`
  [15], `seed` [0], `modulation` [`"qpsk"`] (`"qpsk"`, `"qam16"`, `"psk8"`, `"qam64"`, `"fsk2"`
  or `"fsk4"`, [ADR 0051](adr/0051-psk8-link.md), [ADR 0053](adr/0053-qam64-link.md),
  [ADR 0057](adr/0057-fsk-link.md),
  [ADR 0050](adr/0050-link-modulation.md)), `phase_noise_linewidth_hz` [0] (`≥ 0`,
  [ADR 0047](adr/0047-link-phase-noise.md)), `clock_offset_ppm` [0] (`|·| ≤ 1e5`),
  `timing_loop_gains` [none] and
  `carrier_loop_gains` [none], each none or a pair `[kp, ki]` of numbers `≥ 0`
  ([ADR 0046](adr/0046-link-tracking-loops.md)). Numbers must be finite. **(implemented)**
- **FSK** (`"fsk2"`, `"fsk4"`: `M` = 2 or 4, `k = log2 M`, modulation index 1;
  [ADR 0057](adr/0057-fsk-link.md)) replaces the transmitter and receiver below; the checks above
  still apply, `rrc_taps(rolloff, sps, span_symbols)` must accept its arguments, and `rolloff`,
  `span_symbols` and `phase_block_symbols` are otherwise unused. `samples_per_symbol` must be at
  least `M`; `timing_loop_gains` and `carrier_loop_gains` must be none.
  - Transmitter: `bits = prbs(prbs_order, k·N)`; `tx` = `delay_samples` zeros followed by
    `fsk_modulate(bits, M, sps, 1)`.
  - Channel: as below, but the AWGN is `awgn(·, eb_n0_db + 10·log10 k, sps, signal_power = 1)`.
  - Receiver. `rx` gets zeros appended up to `len(tx) + sps` samples if it is shorter (a clock
    offset can shorten it), so the frame fits at the true offset and the one after it. The
    energy of tone level `a` in the `sps` samples from `d` is
    `E(d, a) = |Σ_{n<sps} rx[d + n]·e^{−jψ(n)}|²`, `ψ(n) = π·(a·n/sps)`, as
    `fsk_demod_noncoherent` computes it.
    1. Timing: `τ` is the first `t` in `0 … sps − 1` that maximizes
       `g(t) = Σ_j max_a E(t + j·sps, a)` over every `j ≥ 0` with `t + (j + 1)·sps ≤ len(rx)` (the
       detector's energy over the whole stream; `a` over the `M` levels).
    2. Frame: with `a_i` the tone level of symbol `i` (conventions: Bits and symbols, FSK), `d₀`
       is the first `d` in `τ, τ + sps, …, ≤ len(rx) − N·sps` that maximizes
       `q(d) = Σ_{i<P} E(d + i·sps, a_i)`.
    3. The decided bits are `fsk_demod_noncoherent(rx[d₀ : d₀ + N·sps], M, sps, 1)`, compared
       with `bits` by `bit_errors`; the preamble counts.
    The preamble alone does not fix the timing to a sample: with continuous phase the first
    sample of a symbol also continues the tone before it, so `q(delay + 1) = q(delay)` when
    noiseless, and `q(delay − 1)` is only a few percent lower. Offsets `delay` and `delay + 1`
    decide the same bits; earlier ones cost many. Timing from the whole stream first, as the
    PSK chain does, keeps a short preamble's noise out of the sample choice. Noiseless, `g(delay
    mod sps)` beats `g(delay + 1 mod sps)` by `2·(sps − 1)`.
  - Report: `timing_offset = d₀ mod sps` (as a float), `frame_start = ⌊d₀/sps⌋`,
    `frequency_offset_hz`, `phase_offset` and `evm` none, `ber_theory = fsk_ber_theory(eb_n0_db,
    M)` or none without noise. Noiseless and without carrier or clock offset, `d₀ =
    delay_samples` and there are no bit errors.
  **(implemented)**
- **Transmitter:** with `k` bits per symbol (2 for QPSK, 4 for 16-QAM, 3 for 8-PSK, 6 for
  64-QAM), `bits = prbs(prbs_order, k·num_symbols)`, `a = qpsk_map(bits)`, `qam16_map(bits)`,
  `psk8_map(bits)` or `qam64_map(bits)`,
  `h = rrc_taps(rolloff, sps, span_symbols)`, `tx` = `delay_samples` zeros followed by
  `pulse_shape(a, h, sps)`. **(implemented)**
- **Channel:** `frequency_offset(tx, frequency_offset_hz, symbol_rate·sps, phase)`, then, with
  `phase_noise_linewidth_hz > 0`, `phase_noise(·, phase_noise_linewidth_hz, symbol_rate·sps)`,
  then, with `clock_offset_ppm ≠ 0`, `clock_offset(·, clock_offset_ppm)` (the receiver's clock), then, with
  `eb_n0_db`, `awgn(·, eb_n0_db + 10·log10 k, sps, signal_power = 1/sps)` (the shaped
  signal's nominal power). One generator seeded with `seed` drives the phase noise and then the
  AWGN, so without phase noise the AWGN is the same as before. **(implemented)**
- **Receiver**, with `N = num_symbols`, `P = preamble_symbols`, `B = phase_block_symbols`:
  1. `y = convolve(rx, h)`; `τ = timing_offset(y, sps)`; `r = y[round(τ) mod sps :: sps]`
     (round half to even). With `timing_loop_gains = [kp, ki]`, instead
     `r = gardner_timing(y, sps, kp, ki, start=τ).symbols`.
  2. `f₁ = qpsk_frequency_offset(r, symbol_rate)`, or for 16-QAM
     `power_frequency_offset(r, symbol_rate, 4)` ([ADR 0049](adr/0049-power-frequency-offset.md));
     `c = frequency_offset(r, −f₁, symbol_rate)`. Steps 4–6 are the same for 16-QAM: its `E[s⁴]`
     is a negative real (−0.68) as QPSK's is (−1), so the block phases and their π/2 ambiguity are
     the same, and so are they for 64-QAM (`E[s⁴] = 2·E[I⁴] − 6·E[I²]² = −0.62`), which uses
     power 4 like 16-QAM. For 8-PSK, `f₁ = power_frequency_offset(r, symbol_rate, 8)`, step 4 uses
     `psk8_block_phases`, and step 6 rounds to multiples of π/4 instead of π/2.
  3. Frame start `k₀`: the first `k` in `0 … len(r) − N` that maximizes
     `|Σ_{i<P} conj(a[i])·c[k+i]|`.
  4. `z = frequency_offset(r[k₀ : k₀+N], −f₁, symbol_rate)`; `φ_b = qpsk_block_phases(z, B)` at
     `x_b` = the middle of block `b`, `(first + last)/2`.
  5. With more than one block, the least-squares line `φ ≈ φ₀ + s·x`:
     `s = Σ(x−x̄)(φ−φ̄) / Σ(x−x̄)²`, `φ₀ = φ̄ − s·x̄`; with one block, `s = 0` and `φ₀ = φ_0`.
  6. `m = round(arg(Σ_{i<P} conj(a[i])·z[i]·e^{−j(φ₀ + s·i)}) / (π/2))` (half to even);
     the phase is `φ = φ₀ + m·π/2` wrapped into `(−π, π]`, and the frequency
     `f = f₁ + s·symbol_rate/(2π)`.
  7. The symbols are `frequency_offset(r[k₀ : k₀+N], −f, symbol_rate, −φ)`. With
     `carrier_loop_gains = [kp, ki]` they are instead `qpsk_carrier_tracking(w, kp, ki,
     phase=φ_p).symbols` (`qam16_carrier_tracking` for 16-QAM, `psk8_carrier_tracking` for
     8-PSK, `qam64_carrier_tracking` for 64-QAM) with `w = frequency_offset(r[k₀ : k₀+N], −f, symbol_rate)` and
     `φ_p = arg(Σ_{i<P} conj(a[i])·w[i])`, the preamble's own phase (no π/2 ambiguity, and local
     to the frame start). Either way they are compared with
     `a` by `evm` and, after `qpsk_demap_hard` (`qam16_demap_hard`, `psk8_demap_hard`, `qam64_demap_hard`), with `bits` by `bit_errors`.
     The preamble counts.
  **(implemented)**
- **Report** (`QpskLinkReport`): `config`, `timing_offset` (τ, samples; the loop's start when it
  runs), `frame_start` (`k₀`,
  symbols into `r`), `frequency_offset_hz` (`f`), `phase_offset` (`φ`, rad: the carrier phase at the
  frame's first symbol), `evm` (an EVM record), `bit_errors` (an error-count record), `ber_theory`
  (`qpsk_ber_theory`, `qam16_ber_theory`, `psk8_ber_theory` or `qam64_ber_theory` of
  `eb_n0_db`, or none without noise). For FSK see above: `frequency_offset_hz`, `phase_offset`
  and `evm` are none. **(implemented)**
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
  `r` (real); type `f64`, `f32`, `i32`, `i16`, `i8`, `u32`, `u16` or `u8` (unsigned:
  [ADR 0058](adr/0058-unsigned-sample-types.md)); order `le` or `be`, which `i8` and `u8` omit and
  every other type requires. Anything else (`f16`, `i64`, a missing or extra order) is
  rejected. **(implemented)**
- **Integer scaling**: code `c` of a `b`-bit type is the sample `c / 2^(b−1)`, so full scale is
  1.0 (units `"FS"` if the caller wants to say so). Writing, a sample becomes
  `round(x·2^(b−1))`, rounding half to even; a non-finite sample or a code outside
  `−2^(b−1) … 2^(b−1) − 1` is rejected (nothing is clipped silently, so `+1.0` itself cannot be
  written). Complex samples scale each part. Unsigned types are offset binary: code `u` is the
  sample `(u − 2^(b−1)) / 2^(b−1)`, and writing gives `round(x·2^(b−1)) + 2^(b−1)` (half to even),
  rejected outside `0 … 2^b − 1`: the signed code with its top bit flipped, so the same range and
  step as the signed type. **(implemented)**
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
  - `annotations`: the metadata key `core:annotations` when it is set, otherwise empty (below).
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
  samples, JSON with duplicate keys or the non-standard `NaN`/`Infinity`, `annotations: null`, and
  a global field named `core:annotations`. Other global fields go to `metadata` under their own
  names; the rest of each capture is not read.
  JSON numbers without a fraction or exponent are integers (`int` / `long`), others floats;
  writing, a float always gets a fraction or an exponent (`2.0`, not `2`), so the kind survives a
  trip through the other language. `captures` and `signalforge:metadata` may be missing, but `null`
  is not an array or an object and is rejected. A missing or unreadable file is an OS error
  (`OSError` / `IOException`), not `invalid_argument`. **(implemented)**
- **Annotations** ([ADR 0061](adr/0061-sigmf-annotations.md)): the metadata key
  `core:annotations` is a list of JSON objects, written to the top-level `annotations` array (not
  to `global`) and read back from it, in file order; an empty or missing array gives no key. Each
  needs `core:sample_start`, an integer ≥ 0, and may have `core:sample_count`, an integer ≥ 0
  (a bool or `2.0` is not an integer); other fields are kept as they are. The list must be sorted
  by `core:sample_start` (ties in any order); unsorted is rejected on writing and reading, not
  sorted. Whether an annotation runs past the samples is not checked. **(implemented)**
- **JSON limits**, the same reading and writing, so whatever one language writes the other reads:
  integers within signed 64 bits (`−2^63 … 2^63 − 1`); floats finite (a literal that overflows a
  double, such as `1e400`, is rejected, not read as infinity); strings and keys valid Unicode (no
  unpaired surrogate, written or as a `\u` escape); objects and arrays nested at most 64 levels
  (`MAX_DEPTH` / `SignalFiles.MaxDepth`), the top object being level 1, so a metadata value
  without a `:` (inside `signalforge:metadata`) starts at level 4 and one with a `:` at level 3.
  Writing checks everything before either file is touched, so a rejected write leaves an existing
  recording as it was. **(implemented)**
- **WAV** ([ADR 0055](adr/0055-wav.md)): `write_wav(path, channels, sample_format="f32")`,
  `read_wav(path)` (C# `WriteWav`, `ReadWav`). A file is a list of real signals, one per channel.
  - Sample formats: `u8`, `i16`, `i24`, `i32` (PCM, little-endian two's complement except `u8`,
    which is unsigned: code `u` is the sample `(u − 128)/128`) and `f32`, `f64` (IEEE float,
    little-endian). Integer scaling, rounding and the rejected range are those of **Integer
    scaling** above; floats as **Floats** above (non-finite values stored as they are).
  - Writing: `channels` is one `Signal` or a non-empty list of them, all real, with the same
    length and the same sample rate, which must be a whole number from 1 to `2^32 − 1`. Block
    align (channels × bytes per sample) must fit 16 bits, the byte rate (sample rate × block
    align) and the RIFF size 32 bits. Samples are interleaved frame by
    frame (channel 0 first). Bytes, all little-endian: `RIFF`, the size of the rest, `WAVE`; a
    `fmt ` chunk with format tag, channels, sample rate, byte rate, block align (channels × bytes
    per sample) and bits per sample, 16 bytes for PCM (tag 1) or 18 for float (tag 3, then
    `cbSize` 0); for float, a `fact` chunk holding the number of frames; then `data`, padded with a
    zero byte to an even length (the pad is counted in the RIFF size, not the data size). Units,
    impedance, center frequency, time origin and metadata are not stored.
  - Reading: `RIFF` and `WAVE` are required, the RIFF size is ignored. Chunks follow from byte 12,
    each an id, a 32-bit size and the body, padded to even; unknown ones are skipped. The first
    `fmt ` must come before the first `data`, which ends the walk. `fmt ` is at least 16 bytes;
    tag 1 takes 8, 16, 24 or 32 bits, tag 3 takes 32 or 64, and tag `0xFFFE` (extensible, at least
    40 bytes) takes either by its sub-format GUID (`01 00` or `03 00` then
    `00 00 00 00 10 00 80 00 00 AA 00 38 9B 71`), its valid-bits and channel-mask fields not read.
    Channels and sample rate must be at least 1 and block align must be channels × bits / 8; the
    byte rate is not checked. Rejected: anything else, a chunk running past the end of the file,
    and a data size that is not whole frames. Each signal has units `"FS"`, center frequency 0,
    time origin 0, no metadata. A missing file is an OS error, as for SigMF. **(implemented)**
- **NumPy `.npy`** ([ADR 0056](adr/0056-npy.md)): `write_npy(path, x)`, `read_npy(path)` (C#
  `WriteNpy`, `ReadNpy<T>`), for 1-D arrays of `float64` (descr `'<f8'`) or `complex128`
  (`'<c16'`, real then imaginary part, each little-endian binary64). Values are stored as they
  are, NaN and ±inf included; a NaN keeps its bits, and the two languages' default NaNs differ in
  the sign bit, so shared write vectors use only infinities.
  - Writing: the bytes `93 'NUMPY' 01 00`, the header length 118 as a little-endian 16-bit
    number, then the header text `{'descr': '<f8', 'fortran_order': False, 'shape': (n,), }`
    (`n` in decimal, `'<c16'` for complex), spaces, and a newline, so the data starts at byte 128;
    then the data. A real `x` of any numeric type is written as `'<f8'`.
  - Reading: the magic, then version 1.0 (16-bit header length), 2.0 or 3.0 (32-bit); the header
    must be ASCII. Its grammar, whitespace (space, tab, CR, LF) allowed between tokens and after
    the dict: `{` entries separated by `,`, an optional trailing `,`, `}`; an entry is a key
    string, `:`, a value; a string is `'…'` or `"…"` with no backslash or that quote inside; a
    value is a string, `True`, `False` or a tuple; a tuple is `(` integers separated by `,` `)`,
    and a single integer needs its trailing `,`; an integer is decimal digits without a leading
    zero (other than `0` itself). The keys are exactly `descr`, `fortran_order` (a bool, either
    value) and `shape`, each once. Rejected: anything else, a descr other than `'<f8'` and
    `'<c16'`, a shape that is not one integer, and a data size other than `n` × 8 or 16 bytes.
    In C# a file of the other kind than `T` is rejected. A missing file is an OS error.
    **(implemented)**

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
