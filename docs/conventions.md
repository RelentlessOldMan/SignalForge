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
  ±1 square) has 0 dB; a real sine has 3.0103 dB. **(implemented)**
- **Single-tone frequency (Kay)** ([ADR 0123](adr/0123-kay-frequency.md);
  `kay_frequency(samples, sample_rate)`, C# `Measurements.KayFrequency`): `Δ_n = atan2` of
  `z_n = x[n+1]·conj x[n]`, written `(ac + bd) + i(bc − ad)`, for `n = 0 … N − 2`; weights
  `w_n = 3N/(2(N² − 1))·(1 − ((n − (N/2 − 1))/(N/2))²)` (sum 1); `f = fs·Σ w_n Δ_n / (2π)` Hz.
  At least two samples, all finite and non-zero; `sample_rate` finite and positive.
  **(implemented)**
- **Zero-crossing rate** ([ADR 0146](adr/0146-zero-crossing-rate.md);
  `zero_crossing_rate(samples)`, C# `Measurements.ZeroCrossingRate`): a sample is positive when
  `x ≥ 0` (so 0 and −0.0 are positive), negative otherwise; `rate = #{n : sign x[n] ≠ sign
  x[n+1]} / (N − 1)`, per adjacent pair, from 0 to 1. Real, finite, at least two samples.
  **(implemented)**
- **Temporal centroid** ([ADR 0147](adr/0147-temporal-centroid.md);
  `temporal_centroid(samples, sample_rate)`, C# `Measurements.TemporalCentroid`): weights
  `p_n = |x[n]|²` at `t_n = n / fs` (sample 0 at t = 0); `centroid = Σ p t / Σ p` and
  `spread = sqrt(Σ p (t − centroid)² / Σ p)`, both in seconds. Gives `TemporalCentroid(centroid,
  spread)`. Real or complex, finite, at least one sample, energy above 0; `sample_rate` finite
  and positive. **(implemented)**
- **Autocorrelation pitch** ([ADR 0150](adr/0150-autocorrelation-pitch.md);
  `autocorrelation_pitch(samples, sample_rate, min_frequency, max_frequency)`, C#
  `Measurements.AutocorrelationPitch`): biased `r` (Autocorrelation); lags `lo = ceil(fs/max)`
  to `hi = floor(fs/min)`, `lo ≤ hi ≤ N − 2`; `L` the largest `r[L]` there (ties: smallest
  lag); if `r[L] ≥` both neighbours and `c = r[L−1] − 2r[L] + r[L+1] < 0`, `δ = (r[L−1] −
  r[L+1]) / (2c)`, else 0. `lag = L + δ`, `frequency = fs / lag`, `voicing = r[L]/r[0]`. Gives
  `AutocorrelationPitch(frequency, lag, voicing)`. Real, finite, `N ≥ 3`, energy above 0;
  `sample_rate` finite and positive; `0 < min ≤ max`, finite. **(implemented)**
- **Cepstrum pitch** ([ADR 0152](adr/0152-cepstrum-pitch.md);
  `cepstrum_pitch(samples, sample_rate, min_frequency, max_frequency, nfft=None)`, C#
  `Measurements.CepstrumPitch`): `c = real_cepstrum(samples, nfft)`, `M = nfft` (default `N`);
  quefrencies `lo = ceil(fs/max)` to `hi = floor(fs/min)`, `lo ≤ hi`, `2·hi < M`; peak, ties
  and parabola exactly as Autocorrelation pitch. `quefrency = L + δ`, `frequency = fs /
  quefrency`, `strength = c[L]`. Gives `CepstrumPitch(frequency, quefrency, strength)`. The
  rules of the real cepstrum, plus `sample_rate` finite and positive and `0 < min ≤ max`,
  finite. **(implemented)**
- **Power CCDF** ([ADR 0119](adr/0119-power-ccdf.md); `power_ccdf(samples, levels_db)`, C#
  `Measurements.PowerCcdf`): for each level `L` dB, `#{n : |x[n]|² > P̄·10^{L/10}} / N`, strict, with
  `P̄` the mean power; result `PowerCcdf(mean_power, levels_db, probabilities)` in the order given.
  `power_ccdf_level(samples, probability)` (C# `Measurements.PowerCcdfLevel`) is the smallest
  level whose CCDF is at most `probability`: `10·log10(p_(m+1)/P̄)`, `p_(m+1)` the
  `(m + 1)`-th largest power, `m = ⌊probability·N⌋` (`−∞` for a zero power). Samples 1-D,
  non-empty, finite, `P̄ > 0`; levels a non-empty list of finite values; `0 < probability < 1`.
  **(implemented)**
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
- **Mel scale** (`hz_to_mel(hz, *, scale="htk")`, `mel_to_hz`, C# `Units.HzToMel`,
  `Units.MelToHz`, [ADR 0154](adr/0154-mel-scale.md)): HTK `m = 2595·log10(1 + f/700)`, inverse
  `700·(10^(m/2595) − 1)`; Slaney `m = f/(200/3)` below 1000 Hz, `15 + ln(f/1000)/(ln 6.4/27)`
  from 1000 Hz, inverse `(200/3)·m` below 15 mel, `1000·exp((m − 15)·ln 6.4/27)` from 15. Values
  finite and `≥ 0`; `scale` is `"htk"` or `"slaney"`. **(implemented)**

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
- **DPSS tapers** (`dpss_tapers(length, half_bandwidth, num_tapers=None)` → `TaperSet(tapers,
  concentrations)`, [ADR 0078](adr/0078-multitaper.md)): `N = length ≥ 1`, `NW = half_bandwidth`
  finite with `0 < NW < N/2`, `W = NW/N`; `K = num_tapers` with `1 ≤ K ≤ N`, default
  `max(1, ⌊2NW⌋ − 1)`.
  - The tridiagonal matrix `T` (`N × N`, symmetric): `T[n][n] = ((N − 1)/2 − n)²·cos(2πW)` and
    `T[n−1][n] = T[n][n−1] = n·(N − n)/2` for `n = 1 … N − 1`.
  - Taper `k = 0 … K − 1` is the eigenvector of `T` for its `(k + 1)`-th largest eigenvalue, with
    `Σ_n v_k[n]² = 1` and the sign that makes `Σ_n v_k[n] > 0` for even `k` and
    `Σ_n ((N − 1)/2 − n)·v_k[n] > 0` for odd `k`. Each value is accurate to about `1e-12`; how it
    is computed is not part of the convention.
  - `tapers` has `K` rows of `N` values (Python a 2-D array, C# an array of rows).
  - Concentration `λ_k = Σ_n Σ_m v[n]·A[n][m]·v[m]`, `A[n][m] = sin(2πW(n − m))/(π(n − m))`,
    `A[n][n] = 2W`: the fraction of the taper's energy in `[−W, W]` (cycles per sample), equal to
    `2W·r_0 + 2·Σ_{d=1}^{N−1} (sin(2πWd)/(πd))·r_d` with `r_d = Σ_{n=0}^{N−1−d} v[n]·v[n + d]`,
    accurate to about `1e-12`.
  - By hand: `N = 1` gives `[[1]]` with `λ = 2W`; `N = 2` gives `(1, 1)/√2` with `λ = 2W +
    sin(2πW)/π` and `(1, −1)/√2` with `λ = 2W − sin(2πW)/π`.
  **(implemented)**
- **Multitaper PSD** (`multitaper_psd(samples, sample_rate, half_bandwidth, *, num_tapers=None,
  one_sided=None, nfft=None, adaptive=False)`, [ADR 0078](adr/0078-multitaper.md)): with `N` the input length and
  the `K` tapers `dpss_tapers(N, half_bandwidth, num_tapers)`, the two-sided PSD is
  `S[k] = (1/K)·Σ_j |X_j[k]|²/fs`, `X_j` the length-`M` DFT (`M = nfft ≥ N`, default `N`, zero
  padded at the end) of `v_j[n]·x[n]`, the sum in order of `j`. Since `Σv² = 1` this is the Welch
  scaling. Sidedness, folding and the frequency axis are as for the PSD above. The result is a
  PSD with `nperseg = N`, `num_segments = K`, `bin_width = fs/M`, `enbw_hz = 2W·fs` and the PSD's
  `span`.
  With `adaptive=True` ([ADR 0079](adr/0079-adaptive-multitaper.md)), Thomson's adaptive weights
  replace the plain mean, bin by bin on the two-sided FFT-order bins before folding. With the
  eigenspectra `S_j[k] = |X_j[k]|²/fs`, the concentrations `λ_j` and `σ² = Σ|x[n]|²/N`, start at
  `S = (S_0 + S_1)/2` (`S_0` when `K = 1`) and repeat
  `S' = Σ_j w_j·S_j / Σ_j w_j`, `w_j = λ_j / (λ_j·S + (1 − λ_j)·σ²/fs)²` (Thomson's `d_j²` with
  the common factor `S²` taken out), sums in order of `j`, until `|S' − S| ≤ 1e-10·S'` or 1000
  repeats, taking `S'` each time; a bin whose `S` is 0 stays 0 (the limit as `S → 0`, which puts
  the weight on the most concentrated taper), and all-zero input gives zeros. Each bin iterates on
  its own. With `K = 1` this is the plain estimate. `num_segments` stays `K` and `enbw_hz` `2W·fs`.
  **(implemented)**
- **Harmonic F-test** (`harmonic_f_test(samples, sample_rate, half_bandwidth, *,
  num_tapers=None, nfft=None)` → `HarmonicFTest(frequencies, amplitudes, f_statistic, p_values,
  num_tapers)`, C# `HarmonicFTestResult`, [ADR 0080](adr/0080-harmonic-f-test.md)). The tapers,
  `M` and `X_j` are as for the multitaper PSD, and `K ≥ 2`. With `U_j = Σ_n v_j[n]` (the computed
  sum), each bin has `μ = Σ_j U_j·X_j / Σ_j U_j²` and
  `F = (K − 1)·|μ|²·Σ_j U_j² / Σ_j |X_j − μ·U_j|²`, with all sums in order of `j`. Its p-value is
  `p = (1 + F/(K − 1))^−(K−1)`, the F(2, 2K − 2) upper tail. When the residual sum is exactly 0,
  `F = +∞` and `p = 0`, or `F = 0` and `p = 1` if `μ = 0` as well. `μ` is the complex amplitude of
  `μ·e^{2πi f n/fs}` with `n` counted from 0. Real input gives bins `0 … ⌊M/2⌋` with frequencies
  `b·fs/M`. Complex input gives all `M` bins on the PSD's two-sided axis. Nothing is folded or
  scaled by `fs`. **(implemented)**
- **Multitaper line removal** (`multitaper_line_removal(samples, sample_rate, half_bandwidth, *,
  probability=None, num_tapers=None, one_sided=None, nfft=None, adaptive=False)` →
  `LineRemoval(spectrum, line_frequencies, line_amplitudes, residual)`, C# `LineRemovalResult`,
  [ADR 0083](adr/0083-multitaper-line-removal.md)).
  - Detection: a bin of the harmonic F-test is a line when `p < probability` (default `1/N`,
    range `(0, 1]`) and its `F` is the largest within `r = ⌊NW·M/N⌋` bins either side. Bins are
    taken circularly mod `M`. For real input a bin past `M/2` stands for its mirror. A tie goes
    to the bin first in the returned order.
  - Removal: every line comes off the samples at once, using the F-test's `μ`. For complex input
    that is `μ·e^{iθ}`. For real input at `0 < b < M/2` it is `2·Re(μ·e^{iθ})`. At DC and at
    `b = M/2` it is `Re μ·cos θ`. Here `θ = 2π·((b·n) mod M)/M`.
  - Outputs: `spectrum` is `multitaper_psd` of the residual with the same arguments. The lines'
    frequencies and `μ` are in the returned order. **(implemented)**
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
- **Generalized Lomb-Scargle** (`generalized_lomb_scargle(times, values, frequencies, *,
  uncertainties=None, normalization="standard")`, [ADR 0081](adr/0081-generalized-lomb-scargle.md)).
  `times`, `values` and `frequencies` are as for the classic form. `uncertainties` are finite
  `σₙ > 0`, one per sample (default all 1). With `W = Σ 1/σₙ²` and `wₙ = (1/σₙ²)/W`, write
  `⟨ab⟩ = Σ wₙaₙbₙ − (Σ wₙaₙ)(Σ wₙbₙ)` for the weighted centered sums. For each `f`, `ω = 2πf`,
  using the cosines and sines at τ = 0, `τ = atan2(2⟨cs⟩, ⟨cc⟩ − ⟨ss⟩)/(2ω)` (any τ when both
  are 0). Then, with `c = cos ω(t − τ)` and `s = sin ω(t − τ)`,
  `p = (⟨yc⟩²/⟨cc⟩ + ⟨ys⟩²/⟨ss⟩)/⟨yy⟩`, where a term whose denominator is below `1e-12` is 0.
  `"standard"` returns `p` and needs `⟨yy⟩ > 0`. `"power"` returns `½·W·⟨yy⟩·p`. `p` equals
  `(χ²₀ − χ²)/χ²₀` of the weighted fit of `a cos ωt + b sin ωt + c`, with `χ²₀` the weighted scatter
  about the weighted mean. With unit σ on even samples at a bin it equals the classic centered
  form. **(implemented)**
- **Multiterm Lomb-Scargle** (`lomb_scargle_multiterm(times, values, frequencies, terms, *,
  uncertainties=None, normalization="standard")`, [ADR 0103](adr/0103-multiterm-lomb-scargle.md)).
  Arguments as for the generalized form, plus `terms`, an integer `≥ 1`. For each `f`, the
  weighted fit of `c + Σₖ aₖ cos kωt + bₖ sin kωt`, `k = 1 … terms`, by modified Gram-Schmidt with
  `⟨a, b⟩ = Σ wₙaₙbₙ`. The columns are taken in the order `cos ωt, sin ωt, cos 2ωt, …`, with the
  argument `(ω·k)·t`, each with its weighted mean subtracted. Each has its projections onto the
  kept columns removed in order, `q ← q − (⟨q, qᵢ⟩/⟨qᵢ, qᵢ⟩)qᵢ`, and is dropped if
  `⟨q, q⟩ < 1e-12`. With `S` the sum of `⟨y_c, q⟩²/⟨q, q⟩` over the kept columns (`y_c` the
  centered values), `"standard"` returns `S/YY` (needs values not all equal) and `"power"` `½·W·S`. That is
  `(χ²₀ − χ²)/χ²₀` and `½(χ²₀ − χ²)`. `terms = 1` is the generalized form to rounding.
  **(implemented)**
- **Lomb-Scargle false-alarm probability** (`lomb_scargle_false_alarm(power, num_samples,
  num_frequencies=1, center=True)`, [ADR 0062](adr/0062-lomb-scargle-significance.md)), for the
  standard normalization: `P₁ = (1 − z)^((N − d)/2)` with `d = 3` centered, `2` not (the Beta
  survival of white Gaussian noise at one frequency), then `−expm1(M·log1p(−P₁))` for `M`
  independent frequencies. `z` in `[0, 1]`, integers `N ≥ d + 1` and `M ≥ 1`; otherwise
  `invalid_argument`. Exact when the fitted cosine and sine are orthogonal to the constant (not
  centered, or evenly spaced times at a bin), close otherwise. **(implemented)**
- **Lomb-Scargle false-alarm level** (`lomb_scargle_false_alarm_level(probability, num_samples,
  num_frequencies=1, center=True)`, [ADR 0082](adr/0082-lomb-scargle-false-alarm-level.md)) is the
  inverse of the false-alarm probability. It computes `P₁ = −expm1(log1p(−p)/M)`, then
  `z = −expm1(2·log(P₁)/(N − d))`. `p = 0` gives 1 and `p = 1` gives 0. `p` is in `[0, 1]`,
  and `N`, `M` and `d` are as for the false-alarm probability; otherwise the call raises
  `invalid_argument`. With `center=True` it also holds for the generalized form.
  **(implemented)**
- **Baluev false-alarm probability** (`lomb_scargle_false_alarm_baluev(power, times, max_frequency,
  center=True)`, [ADR 0098](adr/0098-lomb-scargle-baluev.md)) is for a search of the standard
  normalization up to `f_max`. Let `d = 3, h = 1` when centered and `d = 2, h = 0` when not,
  `N_K = N − d` and `N_H = N − h`. Then `P₁ = (1 − z)^(N_K/2)`, `D = Σ(t − t̄)²/N`,
  `W = f_max·√(4πD)` and `γ = √(2/N_H)·r(N_H)`. Here `r(n) = Γ(n/2)/Γ((n − 1)/2)` comes from
  `r(2) = 1/√π`, `r(3) = √π/2` and `r(n + 2) = r(n)·n/(n − 1)`. Next,
  `τ = W·γ·(1 − z)^((N_K − 1)/2)·√(N_H·z/2)`, and the result is `−expm1(log1p(−P₁) − τ)`, which is 1
  when `P₁ = 1`. `z` must be in `[0, 1]`, there must be at least `d + 1` finite times that are not
  all equal, and `f_max` must be positive and finite; otherwise the call raises `invalid_argument`.
  **(implemented)**
- **Baluev false-alarm level** (`lomb_scargle_false_alarm_level_baluev(probability, times,
  max_frequency, center=True)`, [ADR 0099](adr/0099-lomb-scargle-baluev-level.md)) is the inverse
  of the Baluev probability `F`. It bisects from `lo = 0` and `hi = 1`. At each step it takes
  `m = lo + (hi − lo)/2` and stops when `m` equals `lo` or `hi`. Otherwise it sets `lo = m` if
  `F(m) > p` and `hi = m` if not. It returns `hi`. `p = 1` returns 0 directly. `p = 0` gives 1, and
  so does any `p` that every visited `F(m)` exceeds. `F` is not monotone at `N = d + 1`, or where it
  is near 1, so the result is the crossing bisection finds. `p` must be in `[0, 1]`; the other arguments are checked as for `F`.
  **(implemented)**
- **Lomb-Scargle bootstrap** (`lomb_scargle_bootstrap(times, values, frequencies, draws, *, seed,
  center=True)`, [ADR 0101](adr/0101-lomb-scargle-bootstrap.md)) returns `draws` peaks in draw
  order. Each draw takes `N` indices uniformly with replacement: Python `rng.integers(0, N,
  size=N)`, C# `rng.Next(N)` `N` times. The draw's peak is the largest standard `lomb_scargle` value
  of the values at those indices, at the original times. A draw that cannot be normalized (all
  equal when centered, all zero when not) gives 0. `lomb_scargle`'s checks apply to the original
  values. `frequencies` must not be empty and `draws` must be at least 1. **(implemented)**
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
- **Noise power ratio** (`noise_power_ratio(frequencies, psd, band, notch, span=None)`,
  [ADR 0118](adr/0118-noise-power-ratio.md)): `band = (b_lo, b_hi)` is the loaded band and
  `notch = (n_lo, n_hi)` the notch, finite, with `b_lo < n_lo < n_hi < b_hi`. By the channel power
  rule (same `span`), `loaded_density = (P[b_lo, n_lo] + P[n_hi, b_hi]) / ((n_lo − b_lo) + (b_hi −
  n_hi))` and `notch_density = P[n_lo, n_hi] / (n_hi − n_lo)`. Result `NoisePowerRatio`:
  `loaded_density`, `notch_density`, `npr_db = 10·log10 loaded_density − 10·log10 notch_density`
  (`+∞` for an empty notch). The band lies inside the spectrum as ACPR's channels do (same
  slack); `loaded_density > 0` required. **(implemented)**
- **Spectral flatness** (`spectral_flatness(frequencies, psd, band=None, span=None)`,
  [ADR 0120](adr/0120-spectral-flatness.md)): over the channel power rule's bins (same `span`),
  bin `k` has density `d_k = P_k / (right_k − left_k)` and weight `w_k`, the width of its overlap
  with `band = (low, high)` (default: the whole spectrum). With `W = Σ w_k`: `G = exp(Σ w_k ln d_k
  / W)`, `A = Σ w_k d_k / W`; result `SpectralFlatness(geometric_mean, arithmetic_mean, flatness =
  G/A, flatness_db = 10·log10(G/A))`, `0` and `−∞` dB when a weighted bin is zero. Band edges
  finite, `low < high`, inside the spectrum as ACPR's channels are (same slack); `A > 0` required.
  **(implemented)**
- **Spectral crest factor** (`spectral_crest(frequencies, psd, band=None, span=None)`,
  [ADR 0125](adr/0125-spectral-crest.md)): on the spectral flatness's bins, densities `d_k` and
  overlap weights `w_k`: `mean = Σ w_k d_k / Σ w_k`, `peak = max d_k` over bins with `w_k > 0`;
  result `SpectralCrest(peak, mean, crest = peak/mean, crest_db = 10·log10(peak) −
  10·log10(mean))`. Band rules as for spectral flatness; `mean > 0` required. **(implemented)**
- **Spectral centroid and RMS bandwidth** (`spectral_moments(frequencies, psd, band=None,
  span=None)`, [ADR 0121](adr/0121-spectral-moments.md)): the PSD is a step density, `d_k = P_k /
  (right_k − left_k)` on each bin of the channel power rule (same `span`); bin `k` overlaps `band`
  (default: the whole spectrum) on `[a_k, b_k]`. `power = Σ d_k (b_k − a_k)`, `centroid = Σ d_k
  (b_k² − a_k²)/2 / power`, `rms_bandwidth = sqrt(Σ d_k ((b_k − c)³ − (a_k − c)³)/3 / power)`
  about the centroid `c`. Result `SpectralMoments(power, centroid, rms_bandwidth)`. A flat band of
  width `B` gives `B/√12`. Band rules as for spectral flatness; `power > 0` required.
  **(implemented)**
- **Spectral rolloff** (`spectral_rolloff(frequencies, psd, fraction, band=None, span=None)`,
  [ADR 0124](adr/0124-spectral-rolloff.md)): on the step density and pieces `[a_k, b_k]` of the
  spectral moments, the target is `fraction·power`; at the first piece whose running sum `S_k`
  (including it) reaches the target, the rolloff is `a_k + (target − S_{k−1})/d_k`, limited to
  `[a_k, b_k]`. `fraction` finite in `(0, 1]`; band rules as for spectral flatness; `power > 0`.
  **(implemented)**
- **Spectral skewness and kurtosis** (`spectral_shape(frequencies, psd, band=None, span=None)`,
  [ADR 0126](adr/0126-spectral-shape.md)): on the step density, pieces and centroid `c` of the
  spectral moments, `m_j = Σ d_k ((b_k − c)^{j+1} − (a_k − c)^{j+1})/(j + 1) / power` for
  `j = 2, 3, 4`; result `SpectralShape(skewness = m3/m2^{3/2}, kurtosis = m4/m2²)`, not excess (a
  flat band gives 0 and 9/5). Band rules as for spectral flatness; `power > 0` and `m2 > 0`.
  **(implemented)**
- **Spectral slope** (`spectral_slope(frequencies, psd, band=None, span=None, db=False)`,
  [ADR 0127](adr/0127-spectral-slope.md)): on the pieces `[a_k, b_k]` of the spectral moments,
  `y_k = d_k` (or `10·log10 d_k` with `db`); the continuous least-squares line over the band,
  `center = (low + high)/2`, `W = high − low`: `level = Σ y_k (b_k − a_k)/W`, `slope = Σ y_k
  ((b_k − center)² − (a_k − center)²)/2 / (W³/12)`. Result `SpectralSlope(center, level,
  slope)`. Band rules as for spectral flatness; power `> 0`, and with `db` every overlapping bin
  `> 0`. **(implemented)**
- **Spectral entropy** (`spectral_entropy(frequencies, psd, band=None, span=None)`,
  [ADR 0128](adr/0128-spectral-entropy.md)): on the step density and pieces of the spectral
  moments, `p_k = d_k / power` per Hz and `q_k = p_k (b_k − a_k)`; `entropy = −Σ q_k ln p_k`
  nats over pieces with `d_k > 0`, `entropy_bandwidth = exp(entropy)` Hz, `normalized =
  entropy_bandwidth / (high − low)`. Result `SpectralEntropy(entropy, entropy_bandwidth,
  normalized)`. Band rules as for spectral flatness; `power > 0`. **(implemented)**
- **Spectral flux** (`spectral_flux(frequencies, previous, current, band=None, span=None,
  normalize=True, rectify=True)`, [ADR 0129](adr/0129-spectral-flux.md)): both frames are step
  densities on the spectral moments' pieces `[a_k, b_k]` (same bins, same `span`); with
  `normalize` each is divided by its own band power; `Δ_k = current_k − previous_k`, `max(Δ_k,
  0)` with `rectify`; `flux = sqrt(Σ Δ_k² (b_k − a_k))`. Band rules as for spectral flatness;
  with `normalize`, each frame's power `> 0`. **(implemented)**
- **Spectral decrease** (`spectral_decrease(frequencies, psd, band=None, span=None)`,
  [ADR 0130](adr/0130-spectral-decrease.md)): on the spectral moments' pieces, with density
  `d_k`, width `w_k` and midpoint `m_k` (piece 0 the first in the band) and bin spacing `δ`,
  `decrease = Σ_{k≥1} (d_k − d_0) w_k δ/(m_k − m_0) / Σ_{k≥1} d_k w_k`; on uncut bins this is
  the library form `Σ (P_k − P_0)/k / Σ P_k`. Band rules as for spectral flatness; at least two
  pieces and positive power after the first. **(implemented)**
- **Spectral variation** (`spectral_variation(frequencies, previous, current, band=None,
  span=None)`, [ADR 0131](adr/0131-spectral-variation.md)): both frames are step densities on
  the spectral moments' pieces (widths `w_k`, same bins and `span`); `variation = 1 − Σ d₀d₁w /
  sqrt(Σ d₀²w · Σ d₁²w)`, in [0, 1]. Band rules as for spectral flatness; each frame's power
  `> 0`. **(implemented)**
- **Spectral irregularity** (`spectral_irregularity(frequencies, psd, band=None,
  span=None)`, [ADR 0132](adr/0132-spectral-irregularity.md)): on the spectral moments' pieces
  with density `d_k` and width `w_k`, `irregularity = Σ_k (d_k − d_{k+1})² (w_k + w_{k+1})/2 /
  Σ_k d_k² w_k`; on uncut bins this is Jensen's `Σ (P_k − P_{k+1})² / Σ P_k²`. Band rules as for
  spectral flatness; at least two pieces and positive power. **(implemented)**
- **Spectral contrast** (`spectral_contrast(frequencies, psd, band=None, span=None,
  fraction=0.2)`, [ADR 0133](adr/0133-spectral-contrast.md)): on the spectral moments' pieces
  with density `d_k` and width `w_k`, band width `W = Σ w_k`; sorted by density, `peak` is the
  mean density over the top `fraction · W` of width and `valley` over the bottom, a straddling
  piece counting only for the width needed; `contrast_db = 10 log10(peak / valley)`, +∞ for a
  zero valley. Result `SpectralContrast(peak, valley, contrast_db)`. `0 < fraction ≤ 1/2`; band
  rules as for spectral flatness; power `> 0`. **(implemented)**
- **Band energy ratio** (`band_energy_ratio(frequencies, psd, split, band=None, span=None)`,
  [ADR 0134](adr/0134-band-energy-ratio.md)): on the band's step density, `low = ∫_{low
  edge}^{split} d df` and `high = ∫_{split}^{high edge} d df`, a straddling bin shared by width;
  `ratio = high / low`, `ratio_db = 10 log10(ratio)`, +∞ for zero `low` and 0 and −∞ for zero
  `high`. Result `BandEnergyRatio(low, high, ratio, ratio_db)`. `split` finite and strictly
  inside the band; band rules as for spectral flatness; power `> 0`. **(implemented)**
- **Harmonic-to-noise ratio** (`harmonic_to_noise(frequencies, psd, fundamental, half_width)`,
  [ADR 0143](adr/0143-harmonic-to-noise.md)): bin `k` carries `psd_k·Δ` and is harmonic when
  `m = ⌊f_k/f0 + 1/2⌋ ≥ 1` and `|f_k − m·f0| ≤ half_width`; every other bin, DC included, is
  noise; whole bins, never split. `ratio = harmonic / noise`, `ratio_db = 10 log10(ratio)`, +∞
  for zero noise, 0 and −∞ for zero harmonic power, both zero `invalid_argument`. Result
  `HarmonicToNoise(harmonic, noise, ratio, ratio_db)`. Bin rules as for the band energy ratio;
  `f0` finite and positive; `0 ≤ half_width < f0/2`. **(implemented)**
- **Spectral peaks** (`spectral_peaks(frequencies, psd, min_prominence=0.0)`,
  [ADR 0135](adr/0135-spectral-peaks.md)): a peak is a maximal run `i..j` of equal PSD values
  with both neighbours strictly lower; the first and last bins never are. `index = ⌊(i +
  j)/2⌋`, `frequency = (f_i + f_j)/2`, `height` the run's value. Each side's base is the lowest
  value from the run out to (not including) the first bin strictly higher than `height`, or to
  the end; `prominence = height − max(bases)`. Kept when `prominence ≥ min_prominence`, in
  order of frequency, as `SpectralPeak(index, frequency, height, prominence)`.
  `min_prominence` finite and `≥ 0`. **(implemented)**
- **Peak interpolation** (`interpolate_peak(frequencies, psd, index, scale="db")`,
  [ADR 0136](adr/0136-peak-interpolation.md)): `α, β, γ` the values at `index − 1, index,
  index + 1`, in `10 log10` for `"db"` or as they are for `"linear"`; `offset = (α − γ)/(2(α −
  2β + γ))` bins; `frequency = f_index + offset·δ`; `height = β − (α − γ)·offset/4`, back in PSD
  units for `"db"`. Needs `1 ≤ index ≤ n − 2`, `β ≥ α, γ`, `α − 2β + γ < 0`, and positive
  values for `"db"`; then `|offset| ≤ 1/2`. Gives `PeakEstimate(frequency, height, offset)`.
  **(implemented)**
- **Find tones** (`find_tones(frequencies, psd, count, min_prominence=0.0, scale="db")`,
  [ADR 0137](adr/0137-find-tones.md)): the `spectral_peaks` sorted by prominence, highest first,
  ties to the lower frequency, the first `count` kept, in that order, as `Tone(index, frequency,
  height, prominence)`. `frequency` and `height` are `interpolate_peak`'s at the peak's index,
  or the peak's grid values when the fit is undefined (flat, or a zero bin on the dB scale).
  `count` an integer `≥ 1`. **(implemented)**
- **Peak widths** (`peak_widths(frequencies, psd, rel_height=0.5, min_prominence=0.0)`,
  [ADR 0138](adr/0138-peak-widths.md)): for each `spectral_peaks` peak, `level = height −
  rel_height·prominence`; walking out from the run's ends to the first bin `k` with `x_k ≤
  level`, the crossing is `k + (level − x_k)/(x_{k+1} − x_k)` bins on the left (mirrored on the
  right), in Hz `f_0 + position·δ`; `width = right − left`. Gives `PeakWidth(index, level, left,
  right, width)`. `0 < rel_height ≤ 1`. **(implemented)**
- **Harmonic series** (`harmonic_series(frequencies, tolerance, max_order=10)`,
  [ADR 0139](adr/0139-harmonic-series.md)): candidates `t_i/m`, `m = 1..max_order`; tone `t`
  matches `c` at `m = ⌊t/c + 1/2⌋` when `1 ≤ m ≤ max_order` and `|t − m·c| ≤ tolerance`. The
  candidate matching most tones wins, ties to the highest; `fundamental = Σ m_i t_i / Σ m_i²`
  over its matches. Gives `HarmonicSeries(fundamental, orders, matched)`, with `orders[i] = 0`
  for an unmatched tone. Tones finite and positive, `tolerance > 0` Hz, `max_order ≥ 1`.
  **(implemented)**
- **Inharmonicity** (`inharmonicity(frequencies, heights, fundamental, orders)`,
  [ADR 0140](adr/0140-inharmonicity.md)): `(2/f0)·Σ h_i |t_i − m_i f0| / Σ h_i` over the tones
  with `m_i ≥ 1`; order 0 is left out. Dimensionless, 0 for exact harmonics. Arrays 1-D of one
  length; tones finite and positive, heights finite and `≥ 0`, orders whole and `≥ 0`, `f0`
  finite and positive; the matched heights must sum to more than 0. **(implemented)**
- **Odd-to-even ratio** (`odd_even_ratio(heights, orders)`,
  [ADR 0141](adr/0141-odd-even-ratio.md)): `Σ h` over odd orders (the fundamental counts as
  odd) over `Σ h` over even orders; order 0 is left out. A plain power ratio. No even power
  with some odd power gives `+inf`; both 0 is `invalid_argument`. Arrays 1-D of one length;
  heights finite and `≥ 0`; orders whole and `≥ 0`. **(implemented)**
- **Tristimulus** (`tristimulus(heights, orders)`, [ADR 0142](adr/0142-tristimulus.md)):
  amplitudes `a = sqrt(h)` from power heights; with `A = Σ a` over orders `≥ 1`, `first` is
  order 1's share, `second` orders 2–4, `third` orders 5 and up; they sum to 1. Order 0 is left
  out. Arrays 1-D of one length; heights finite and `≥ 0`; orders whole and `≥ 0`; `A > 0`.
  **(implemented)**
- **Harmonic deviation** (`harmonic_deviation(heights, orders)`,
  [ADR 0144](adr/0144-harmonic-deviation.md)): `a_m = sqrt(Σ h)` over the tones of order `m`,
  `m = 1..H` (`H` the highest order; duplicates add as powers, a missing order is 0, order 0
  left out); envelope `e_m` the mean of `a_{m−1}, a_m, a_{m+1}` inside `1..H`;
  `deviation = Σ |a_m − e_m| / Σ a_m`. Arrays 1-D of one length; heights finite and `≥ 0`;
  orders whole and `≥ 0`; `Σ a > 0`. **(implemented)**
- **Harmonic centroid** (`harmonic_centroid(frequencies, heights, orders)`,
  [ADR 0145](adr/0145-harmonic-centroid.md)): weights `a_i = sqrt(h_i)` over the tones with
  order `≥ 1`, each at its measured frequency; `centroid = Σ a t / Σ a` and
  `spread = sqrt(Σ a (t − centroid)² / Σ a)`, both in Hz. Gives `HarmonicCentroid(centroid,
  spread)`. Arrays 1-D of one length; tones finite and positive; heights finite and `≥ 0`;
  orders whole and `≥ 0`; the matched amplitudes must sum to more than 0. **(implemented)**
- **Real cepstrum** (`real_cepstrum(samples, nfft=None)`, C# `Spectral.RealCepstrum`,
  [ADR 0151](adr/0151-real-cepstrum.md)): `c = Re IFFT(ln|FFT(x, M)|)`, natural log, `M = nfft`
  (zero padded; default `N`, at least `N`), all `M` values returned. A bin of magnitude exactly
  0 is `invalid_argument` (no floor). Real, finite, at least one sample. **(implemented)**
- **Minimum phase** (`minimum_phase(samples, nfft=None)`, C# `Spectral.MinimumPhase`,
  [ADR 0153](adr/0153-minimum-phase.md)): `c = real_cepstrum(x, M)`; fold `ĉ[0] = c[0]`,
  `ĉ[m] = 2c[m]` for `1 ≤ m ≤ ⌈M/2⌉ − 1`, `ĉ[M/2] = c[M/2]` for even `M`, else 0;
  `y = Re IFFT(exp(FFT(ĉ)))`, all `M` values. `M = nfft ≥ N`; default the smallest power of two
  `≥ max(64, 8N)`. The rules of the real cepstrum. **(implemented)**
- **Mel filterbank** (`mel_filterbank(n_filters, nfft, sample_rate, min_frequency=0.0,
  max_frequency=None, *, scale="htk", area_normalized=False)`, C# `Spectral.MelFilterbank`,
  [ADR 0155](adr/0155-mel-filterbank.md)): edges `m_i = M_lo + (M_hi − M_lo)·i/(n + 1)`,
  `i = 0 … n + 1`, in mel (Mel scale), `f_i = mel_to_hz(m_i)`; max defaults to `fs/2`. Bin
  `b_k = k·fs/nfft`, `k = 0 … nfft//2`. `W[i][k] = max(0, min((b_k − f_i)/(f_{i+1} − f_i),
  (f_{i+2} − b_k)/(f_{i+2} − f_{i+1})))`; `area_normalized` scales row `i` by `2/(f_{i+2} − f_i)`.
  An all-zero row is allowed. `n ≥ 1`, `nfft ≥ 2`, `fs` finite and positive, `0 ≤ min < max ≤
  fs/2`. **(implemented)**
- **DCT-II** (`dct(samples, *, orthonormal=True)`, `idct(coefficients, *, orthonormal=True)`, C#
  `Spectral.Dct`, `Spectral.Idct`, [ADR 0156](adr/0156-dct-ii.md)): `X[k] = s_k Σ x[n] cos(π k
  (2n+1)/(2N))`, orthonormal `s_0 = √(1/N)`, `s_k = √(2/N)`, unnormalized `s_k = 2`. `idct` is
  the exact inverse for the same scaling (orthonormal `x[n] = Σ s_k X[k] cos(…)`; unnormalized
  `x[n] = (X[0]/2 + Σ_{k≥1} X[k] cos(…))/N`). Direct `O(N²)` from one table `cos(πj/(2N))`,
  `j = k(2n+1) mod 4N`. Real, finite, at least one value. **(implemented)**
- **MFCC** (`mfcc(power_spectrum, filterbank, n_coefficients, *, floor=1e-10)`, C#
  `Spectral.Mfcc`, [ADR 0157](adr/0157-mfcc.md)): `E_i = Σ_k W[i][k] P[k]`, `L_i = ln(max(E_i,
  floor))` (natural log), result the first `n_coefficients` of the orthonormal `dct(L)`, `c_0`
  kept, no liftering. Power 1-D, finite, `≥ 0`, at least one bin; filterbank 2-D, at least one
  row, each of `K` finite non-negative weights; `1 ≤ n_coefficients ≤ n_filters`; floor finite
  and positive. **(implemented)**
- **Delta coefficients** (`delta(frames, width=2)`, C# `Spectral.Delta`,
  [ADR 0158](adr/0158-delta-coefficients.md)): per column `d_t = Σ_{n=1}^{W} n (c_{t+n} −
  c_{t−n}) / (2 Σ n²)`, indices outside `0 … T−1` clamped to the nearest frame (HTK); output `T`
  rows. Frames 2-D, at least one row and one column, finite; `width ≥ 1`. **(implemented)**
- **Cepstral liftering** (`cepstral_lifter(coefficients, length=22)`, C#
  `Spectral.CepstralLifter`, [ADR 0159](adr/0159-cepstral-lifter.md)): `c'_n = (1 + (L/2)
  sin(π n / L)) c_n`, `n = 0 …`; one frame, 1-D, real, finite, at least one value; `L ≥ 1`; no
  inverse. **(implemented)**
- **x dB bandwidth** (`db_bandwidth(frequencies, psd, drop_db, band=None)`,
  [ADR 0122](adr/0122-db-bandwidth.md)): over the bins (validated as for channel power, no span)
  whose centers lie in `band = (low, high)` (default: all), the peak is the largest PSD, first on
  ties, and must be positive; `t = peak·10^{−drop_db/10}`. Walking down from the peak to the first
  bin `i` with `psd[i] ≤ t`, the lower edge is `f_i + (t − psd[i])/(psd[i+1] − psd[i])·Δ`, linear
  in power; the upper edge likewise walking up. No crossing on a side is `invalid_argument`.
  Result `DbBandwidth(peak_frequency, peak_psd, lower, upper, bandwidth)`. `drop_db` finite and
  positive; band edges finite, `low < high`, at least one bin in the band. **(implemented)**
- **ACPR through an RRC filter** (`acpr_rrc(frequencies, psd, center, symbol_rate, alpha, offsets,
  span=None)`, [ADR 0111](adr/0111-acpr-rrc.md)): channels centred at `center` and `center ∓ o`,
  each power `Σ psd_k·Δ·G(f_k − c)` with `G` the RRC's `|H|²` at peak 1: `1` for
  `|f| ≤ (1 − α)R/2`, `½(1 + cos(π(|f| − (1 − α)R/2)/(αR)))` up to `(1 + α)R/2`, `0` beyond
  (`R = symbol_rate`). Each support `c ± (1 + α)R/2` inside the spectrum as for ACPR; `R` finite
  `> 0`; `0 < α ≤ 1`; offsets, `main_power > 0` and the result as for ACPR. **(implemented)**
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

## Two-tone intermodulation

Decided in [ADR 0107](adr/0107-two-tone-imd.md). Python: `signalforge.measurements.two_tone_imd`;
C#: `Measurements.TwoToneImd`. Same spectrum, half-width and groups as the tone metrics.

- **Call:** `two_tone_imd(samples, sample_rate, f1, f2, *, window="blackman_harris", beta=None,
  width=None)`, real or complex; `f1 < f2`, both finite and following the fundamental's rules.
  **(implemented)**
- **Groups:** DC, the tone at `f1` (the fundamental), the tone at `f2`, the lower product
  `2f₁ − f₂`, the upper product `2f₂ − f₁`, each at the bin nearest its nominal frequency, the
  products aliased as harmonics are. A centre bin already claimed is `invalid_argument`; so is no
  power in the `f2` group. **(implemented)**
- **Result** (`TwoToneImd`): `tone_frequencies` (centroids), `tone_powers`, `imd_frequencies`
  (the aliased nominal ones, lower first), `imd_powers`, `imd_dbc = 10·log10(P_IM/P_t)` with
  `P_t` the mean tone power (`−∞` for a product with no power), `worst_imd_dbc` (the larger) and
  `ip3_db = 10·log10 P_t − worst_imd_dbc/2`. **(implemented)**
- **Second order** ([ADR 0110](adr/0110-two-tone-ip2.md); `two_tone_ip2`, C#
  `Measurements.TwoToneIp2`): same call, arguments and groups, with the products the difference
  `f₂ − f₁` then the sum `f₁ + f₂` (aliased; third-order products not claimed). Result
  `TwoToneIp2`: the fields above with `ip2_db = 10·log10 P_t − worst_imd_dbc` (`+∞` for no
  product power) in place of `ip3_db`. **(implemented)**
- **Fifth order** ([ADR 0117](adr/0117-two-tone-ip5.md); `two_tone_ip5`, C#
  `Measurements.TwoToneIp5`): same call, arguments and groups, with the products `3f₁ − 2f₂` then
  `3f₂ − 2f₁` (aliased; third-order products not claimed). Result `TwoToneIp5`: the fields above
  with `ip5_db = 10·log10 P_t − worst_imd_dbc/4` (`+∞` for no product power) in place of
  `ip3_db`. **(implemented)**

## Phase noise measurement

Decided in [ADR 0108](adr/0108-phase-noise-measurement.md). Python:
`signalforge.measurements.phase_noise_ssb`; C#: `Measurements.PhaseNoiseSsb`.

- **Call:** `phase_noise_ssb(samples, sample_rate, offsets, *, carrier=None, nperseg=None,
  window="blackman_harris", beta=None, width=None)`, real or complex, at least two samples.
  `offsets` 1-D, non-empty, finite and positive; `carrier` as the tone metrics' fundamental.
  **(implemented)**
- **Spectrum and carrier:** `welch_psd(samples, sample_rate, nperseg=nperseg, window=window,
  beta=beta)`. The carrier bin `k_c` is the first with the largest PSD, or the one nearest
  `carrier`; its group is the bins within `w` of it (the tone metrics' half-width unless `width`
  is given), clipped. `carrier_power` is the group's PSD · bin width summed, `carrier_frequency`
  its power centroid. No DC group. Zero carrier power is `invalid_argument`. **(implemented)**
- **Sidebands:** for each offset `o`, the bins nearest `carrier_frequency ± o`; both frequencies
  within `0 ≤ f ≤ fs/2` (real) or `−fs/2 ≤ f < fs/2` (complex), and both bins with `|k − k_c| > w`, else
  `invalid_argument`. `l_dbc_hz = 10·log10(mean of the two PSD values / carrier_power)`, `−∞`
  when both are zero. **(implemented)**
- **Result** (`PhaseNoise`): `carrier_frequency`, `carrier_power`, `offsets`, `l_dbc_hz`.
  **(implemented)**

## Integrated phase noise

Decided in [ADR 0109](adr/0109-integrated-phase-noise.md). Python:
`signalforge.measurements.integrated_phase_noise`; C#: `Measurements.IntegratedPhaseNoise`.

- **Call:** `integrated_phase_noise(samples, sample_rate, f_lo, f_hi, *, carrier=None,
  nperseg=None, window="blackman_harris", beta=None, width=None)`, real or complex.
  `0 < f_lo < f_hi`, finite. Spectrum, carrier, group, `carrier_power` and `carrier_frequency` as
  for Phase noise measurement. **(implemented)**
- **Band:** the bins with `f_lo ≤ |f_k − carrier_frequency| ≤ f_hi`, both sides, whole bins only.
  `carrier_frequency ± f_hi` within the spectrum as for an offset, and no band bin in the carrier
  group, else `invalid_argument`. **(implemented)**
- **Result** (`IntegratedPhaseNoise`): `carrier_frequency`, `carrier_power`, `f_lo`, `f_hi`;
  `ratio = Σ PSD_k·Δf / carrier_power` over the band; `integrated_dbc = 10·log10 ratio` (`−∞` for
  zero); `phase_rms = √ratio` rad; `jitter_rms = phase_rms/(2π|carrier_frequency|)` s, `+∞` when
  `carrier_frequency = 0` (`0` if `phase_rms` is `0`). **(implemented)**

## Phase noise with spurs removed

Decided in [ADR 0115](adr/0115-phase-noise-spur-removal.md). A keyword `spur_offsets` (C#
`spurOffsets`) on `phase_noise_ssb` and `integrated_phase_noise`.

- **Argument:** 1-D, every offset finite and positive, in Hz from `carrier_frequency`; `None` (C#
  `null`) or empty removes nothing. Spurs are named, not detected. **(implemented)**
- **Removal:** on a copy of the Welch PSD, before the sidebands or the band are read. The offsets
  are taken in the order given; for each, the side `carrier_frequency − o` and then
  `carrier_frequency + o`. A side outside the spectrum (the test for an offset's reach) is
  skipped. Otherwise `s` is the bin nearest it, `w` the carrier group's half-width, and
  `a = s − w − 1`, `b = s + w + 1`. Each bin `j` with `a < j < b` in the spectrum gets
  `p_a + (p_b − p_a)·(j − a)/(2w + 2)`, computed in that order, from the PSD as it stands. An
  edge past the spectrum takes the other edge's value. `|s − k_c| ≤ 2w + 1` is
  `invalid_argument`. **(implemented)**

## Phase noise spur finder

Decided in [ADR 0116](adr/0116-phase-noise-spur-finder.md). Python:
`signalforge.measurements.phase_noise_spurs`; C#: `Measurements.PhaseNoiseSpurs`.

- **Call:** `phase_noise_spurs(samples, sample_rate, f_lo, f_hi, *, threshold_db=10.0,
  carrier=None, nperseg=None, window="blackman_harris", beta=None, width=None)`. The carrier, its
  group and `w` are as for `phase_noise_ssb`. `threshold_db` is finite and positive.
  **(implemented)**
- **Band:** bins with `f_lo ≤ |f_j − carrier_frequency| ≤ f_hi`, both sides; `0 < f_lo < f_hi`,
  finite, not past the spectrum (as `integrated_phase_noise`); a band bin with
  `|j − k_c| ≤ 2w + 1` is `invalid_argument`. **(implemented)**
- **Test:** bin powers `p = psd·bin_width`, those at or below `1e-20` of the total set to zero.
  For band bin `j` with `a = j − w − 1 ≥ 0` and `b = j + w + 1` inside the spectrum (others are
  not tested): `G = Σ_{a<i<b} p_i`, `L = (2w + 1)(p_a + p_b)/2`. `j` is a spur when
  `p_j > p_i` for `j − w ≤ i < j`, `p_j ≥ p_i` for `j < i ≤ j + w`, and
  `G > L·10^(threshold_db/10)`. **(implemented)**
- **Result** (`PhaseNoiseSpurs`): `carrier_frequency`, `carrier_power`; `offsets`
  (`f_j − carrier_frequency`, signed, Hz) and `levels_dbc` (`10·log10((G − L)/carrier_power)`), in
  ascending `j`; empty when there are none. **(implemented)**

## Noise figure

Decided in [ADR 0105](adr/0105-noise-figure-y-factor.md). Python:
`signalforge.measurements.noise_figure_y_factor`; C#: `Measurements.NoiseFigureYFactor`.

- **Call:** `noise_figure_y_factor(hot_power, cold_power, enr_db, *, cold_temperature=290.0)`.
  Linear powers in one unit; `cold_power` finite and positive, `hot_power` finite and above it;
  `enr_db` finite; `cold_temperature` in kelvin, finite and positive. **(implemented)**
- **Formula:** `T₀ = 290 K` fixed, `Y = hot/cold`, `ENR = 10^(enr_db/10)`,
  `F = (ENR − Y·(T_c/T₀ − 1))/(Y − 1)` (so `ENR/(Y − 1)` when `T_c = T₀`). `F` not finite or
  `≤ 0` is `invalid_argument`; `0 < F < 1` is returned. No second-stage correction.
  **(implemented)**
- **Result** (`NoiseFigure`): `y_factor = Y`, `noise_factor = F`, `noise_figure_db = 10·log10 F`,
  `noise_temperature = T₀(F − 1)` in kelvin. **(implemented)**
- **Cascade** (`noise_figure_cascade(noise_figures_db, gains_db)`,
  [ADR 0106](adr/0106-noise-figure-cascade.md)): Friis, one value per stage in chain order.
  `Fᵢ = 10^(NFᵢ/10)`, `Gᵢ = 10^(gᵢ/10)`, `Πᵢ = G₁…Gᵢ₋₁` multiplied in order (`Π₁ = 1`);
  contributions `c₁ = F₁`, `cᵢ = (Fᵢ − 1)/Πᵢ`; `F = Σ cᵢ` in order. Both 1-D, same length `≥ 1`,
  finite; every `NFᵢ ≥ 0`; gains may be negative (losses). `F` not finite is `invalid_argument`.
  Result (`CascadeNoiseFigure`): `noise_factor`, `noise_figure_db`, `noise_temperature`
  (`T₀(F − 1)`), `gain_db` (the `gᵢ` summed in order) and `contributions`. **(implemented)**

## Gain compression

Decided in [ADR 0112](adr/0112-gain-compression.md). Python:
`signalforge.measurements.gain_compression`; C#: `Measurements.GainCompression`.

- **Call:** `gain_compression(input_db, output_db, *, compression_db=1.0, linear_points=1)`: a
  drive sweep's levels in dB of one unit. Both 1-D, the same length `≥ 2`, finite; `input_db`
  strictly ascending; `compression_db` finite `> 0`; `linear_points` whole, `1 … n`.
  **(implemented)**
- **Rule:** `gᵢ = outᵢ − inᵢ`; `G` the mean of the first `linear_points` gains, summed in order;
  `cᵢ = G − gᵢ`. The input point is at the first `k` with `c_k ≥ compression_db`: `in₀` if
  `k = 0`, else `in_{k−1} + (compression_db − c_{k−1})/(c_k − c_{k−1})·(in_k − in_{k−1})`; NaN if
  no step reaches it. Output point `= input point + G − compression_db`. **(implemented)**
- **Result** (`GainCompression`): `small_signal_gain_db`, `gain_db`, `compression`,
  `input_point_db`, `output_point_db`, `saturated_output_db` (the largest `outᵢ`).
  **(implemented)**

## AM/AM and AM/PM

Decided in [ADR 0113](adr/0113-am-am-am-pm.md). Python: `signalforge.measurements.am_am_pm`;
C#: `Measurements.AmAmPm`.

- **Call:** `am_am_pm(input, output, edges_db)`: complex samples of the same length `≥ 1`, finite;
  `edges_db` at least 2 finite, strictly ascending edges in dB of input amplitude.
  **(implemented)**
- **Bins:** a sample's level is `20·log10|xₖ|`; bin `i` holds `eᵢ ≤ L < eᵢ₊₁`, the last bin also
  its upper edge; samples outside every bin (and `x = 0`) are not counted. A level within
  rounding of an edge may fall either side. **(implemented)**
- **Per bin:** `h` the mean of `yₖ/xₖ` summed in order; `gain_db = 20·log10|h|`,
  `phase_deg = atan2(Im h, Re h)·180/π`. An empty bin gives NaN for both and count 0; `h = 0`
  gives `−∞` and 0. **(implemented)**
- **Result** (`AmAmPm`): `levels_db` (each bin's mean edge), `counts`, `gain_db`, `phase_deg`. No
  small-signal reference: the caller subtracts the bin it wants. **(implemented)**

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
- **Autocorrelation** (`autocorrelation(samples, max_lag=None, *, scaling="biased")`, C#
  `Dsp.Autocorrelation`, [ADR 0148](adr/0148-autocorrelation.md)): `r[k] = Σ_{n=0}^{N−1−k}
  x[n+k]·conj x[n]` for `k = 0 … max_lag` (so `r[−k] = conj r[k]`; NumPy's `correlate(x, x)`);
  `"biased"` divides by `N`, `"unbiased"` by `N − k`, `"none"` not at all. The mean is kept.
  Real in, real out. At least one finite sample; `max_lag` an integer in `0 … N − 1`, default
  `N − 1`. **(implemented)**
- **Linear prediction** (`levinson(r, order)`, C# `Dsp.Levinson`,
  [ADR 0149](adr/0149-levinson-durbin.md)): Levinson-Durbin on an autocorrelation `r` (lags
  `0 … order` used). The prediction-error filter `a`, `a[0] = 1`, `order + 1` taps,
  `e[n] = Σ a[j] x[n−j]`, solves `Σ_j a[j] r[i−j] = 0` for `i = 1 … p` with `r[−k] = conj r[k]`.
  Recursion: `k_m = −(r[m] + Σ_{j<m} a[j] r[m−j]) / E`, `a[j] += k_m conj a[m−j]`, `a[m] = k_m`,
  `E *= 1 − |k_m|²`, from `E = r[0]`. Gives `Levinson(coefficients, reflection, error)`. `r`
  finite with `r[0]` real and positive; `order ≥ 1`; every `|k_m| < 1`. **(implemented)**
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
  weights=None, kind="filter")`, [ADR 0029](adr/0029-least-squares-fir.md),
  [ADR 0086](adr/0086-antisymmetric-least-squares.md)): the symmetric taps whose zero-phase
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
  - `kind`: `"filter"` is all of the above. `"hilbert"` and `"differentiator"` give antisymmetric
    taps with equiripple design's `A`: `A(ν) = Σ_{k<L} a_k sin(2π t_k ν)` with `t_k = k + 1`,
    `L = (N − 1)/2` (odd `N`), or `t_k = k + ½`, `L = N/2` (even `N`). Taps: `h[c + t_k] = a_k/2`,
    `h[c − t_k] = −a_k/2` with `c = (N − 1)/2` (the centre tap of an odd `N` is 0).
    `G_kl = Σ_j W_j (C(t_k − t_l) − C(t_k + t_l))/2`. The target is `T_j = D_j` (`"hilbert"`) or
    `T_j = −2πν·D_j` (`"differentiator"`), with the plain weight `W_j` (not equiripple design's
    relative one). With the sine moments `M_i(u) = ∫_α^β ν^i sin(2πuν) dν`, `κ = 2πu`:
    `M_0 = [−cos κν/κ]`, `M_1 = [−ν cos κν/κ + sin κν/κ²]`,
    `M_2 = [−ν² cos κν/κ + 2ν sin κν/κ² + 2 cos κν/κ³]`, each `_α^β`. With `ℓ_j = D_lo − s_j α`:
    `p_k = Σ_j W_j (ℓ_j M_0(t_k) + s_j M_1(t_k))` (`"hilbert"`) or
    `Σ_j W_j (−2π)(ℓ_j M_1(t_k) + s_j M_2(t_k))` (`"differentiator"`). `2 ≤ num_taps ≤ 1001`. A
    nonzero target where the type has `A = 0` (at 0; at fs/2 for odd `N`) is part of the error.
    Any other `kind` is `invalid_argument`.
- **Frequency-sampling design** (`fir_frequency_sampling(num_taps, frequencies, gains,
  sample_rate, window="hamming", beta=None, num_points=None, kind="filter")`,
  [ADR 0084](adr/0084-frequency-sampling-fir.md), [ADR 0085](adr/0085-antisymmetric-frequency-sampling.md)):
  symmetric or antisymmetric taps from a sampled piecewise-linear magnitude.
  - Arguments: `frequencies` in Hz, at least two, finite, strictly increasing, the first exactly
    0 and the last exactly `fs/2`; `gains` one finite value per frequency. `num_taps ≥ 1`; even
    `num_taps` (type II) needs the last gain to be 0. `window` and `beta` as for windowed-sinc
    design (symmetric form). `num_points = K`, an integer in `[2, 2²⁰ + 1]` with
    `L = 2(K − 1) ≥ num_taps`; by default `K − 1` is the smallest power of two `≥ max(num_taps,
    512)`.
  - Grid: `ν_k = k/L` for `k = 0 … K − 1` (so `ν_{K−1} = ½`). `G_k` is the target at `ν_k`: with
    breakpoints `ν_i = f_i/fs`, take the segment `ν_i ≤ ν_k ≤ ν_{i+1}` (the first such `i`) and
    `G_k = g_i + (g_{i+1} − g_i)(ν_k − ν_i)/(ν_{i+1} − ν_i)`.
  - Taps: with `t = n − (N − 1)/2`,
    `d[n] = (1/L)[G_0 + 2 Σ_{k=1}^{K−2} G_k cos(2πkt/L) + G_{K−1} cos(πt)]`. This is the inverse
    `L`-point DFT of `G_k e^{−iπk(N−1)/L}` (the Hermitian extension), which is how a language may
    compute it. Then `h[n] = d[n]·w[n]` with the symmetric window, and `h ← (h + reversed h)/2`,
    which makes the symmetry exact (neither an FFT nor a computed window is symmetric to the last
    bit). No rescaling.
  - A flat gain `c` gives `c` times the unit impulse at the centre for odd `N` (the cosines sum
    to `L·δ(t)`, and the symmetric window's centre is 1).
  - `kind`, as for equiripple design: `"filter"` is all of the above. `"hilbert"` and
    `"differentiator"` give antisymmetric taps with `H = −j·e^(−j2πfc/fs)·A`. Their amplitude
    samples are `A_k = G_k` (`"hilbert"`) or `A_k = −2πν_k·G_k` (`"differentiator"`). The grid
    samples are `−j·e^{−iπk(N−1)/L}·A_k`, so
    `d[n] = (1/L)[2 Σ_{k=1}^{K−2} A_k sin(2πkt/L) + A_{K−1} sin(πt)]`. After the window,
    `h ← (h − reversed h)/2`, which makes the antisymmetry exact (the centre tap of an odd `N` is
    exactly 0). They need `num_taps ≥ 2`. `"hilbert"` needs the first gain to be 0. An odd
    `num_taps` (type III) needs the last gain to be 0 for both kinds. The even-length rule above is
    for `"filter"` only. Any other `kind` is `invalid_argument`.

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
- **Sample clock drift** (`clock_drift(samples, ppm_start, ppm_end, *, half_width=16)`,
  [ADR 0102](adr/0102-clock-drift.md)): the clock offset linear in input time,
  `p(t) = p₀ + (p₁ − p₀)·t/(N − 1)`, each step `1 + p(t_n)/1e6`. With `r = 1 + p₀/1e6` and
  `d = (p₁ − p₀)/1e6/(N − 1)` computed in that order, `t_n = r·expm1(n·log1p(d))/d`, or `n·r` as
  in Sample clock offset when `d = 0` (also for `N ≤ 1`). `y[n] = z(t_n)` through the same kernel
  for `n = 0, 1, …` while `t_n ≤ N − 1` (none for empty input). Both offsets finite with
  `|·| ≤ 1e5`; `half_width` an integer `≥ 1`. **(implemented)**
- **Sample clock jitter** (`clock_jitter(samples, rms, *, seed, half_width=16)`,
  [ADR 0104](adr/0104-clock-jitter.md)): `y[n] = z(n + σ·gₙ)` for `n = 0 … N − 1`, `σ = rms` in
  samples. `gₙ` are independent standard Gaussians drawn in order (Python `standard_normal(N)`,
  C# the Box–Muller cosine branch). `z` is read through the same kernel, `x` zero outside
  `0 … N − 1`. `rms` finite with `0 ≤ rms ≤ 0.5`; `half_width` an integer `≥ 1`. Seeded as for
  AWGN, with streams that differ between languages. `rms = 0` returns the input.
  **(implemented)**
- **Amplifier models** ([ADR 0114](adr/0114-amplifier-models.md)): memoryless, on the complex
  envelope; a real input is `x + 0j`. With `r = |x|`, `y = (x/r)·A(r)·e^{jΦ(r)}` and `x = 0`
  gives 0. Output complex, as long as the input; samples are not checked. **(implemented)**
  - **Saleh** (`saleh_amplifier(samples, alpha_a, beta_a, alpha_phi, beta_phi)`):
    `A(r) = α_a r/(1 + β_a r²)`, `Φ(r) = α_φ r²/(1 + β_φ r²)` radians, computed as
    `y = x·α_a/(1 + β_a r²)·e^{jΦ(r)}`. `α_a > 0`, `β_a ≥ 0`, `β_φ ≥ 0`, `α_φ` any sign, all
    finite. **(implemented)**
  - **Rapp** (`rapp_amplifier(samples, gain, saturation, smoothness)`):
    `A(r) = g r/(1 + (g r/A_sat)^{2p})^{1/(2p)}`, `Φ = 0`. With `u = g r/A_sat`:
    `y = x·g/(1 + u^{2p})^{1/(2p)}` for `u ≤ 1`, `y = (x/r)·A_sat/(1 + u^{−2p})^{1/(2p)}` for
    `u > 1`. `g`, `A_sat`, `p` positive and finite. **(implemented)**

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
- **LMS equalizer** (`lms_equalizer(samples, training, num_taps, step, *, samples_per_symbol=1,
  center=None, decision=None, initial_taps=None)`, [ADR 0066](adr/0066-lms-equalizer.md)): normalized LMS, taps
  fractionally spaced by `sps = samples_per_symbol`. `x` the samples (finite, at least one),
  `L = num_taps ≥ 1`, `c = center` in `0 … L − 1` (default `⌊(L − 1)/2⌋`), `μ = step` finite in
  `[0, 2]`, `t` the training symbols (finite, `T = len(t)` at most the output count). The taps
  start `w_c = 1`, every other `w_i = 0`, or with `initial_taps` (`L` finite values) at those
  ([ADR 0072](adr/0072-least-squares-equalizer-start.md)). For `n = 0 … N − 1`, `N = ⌈len(x)/sps⌉`:
  - the regressor `u_i = x[n·sps + c − i]` for `i = 0 … L − 1`, 0 outside `0 … len(x) − 1`;
  - the output `y_n = Σ_i w_i·u_i`, summed in order of `i`;
  - the reference `d_n = t_n` for `n < T`; for `n ≥ T` with `decision` `"qpsk"`, `"psk8"`,
    `"qam16"` or `"qam64"`, `d_n` is that modulation's map of its hard demap of `y_n`; otherwise
    there is none;
  - with a reference, `e_n = d_n − y_n`, `P = Σ_i |u_i|²` (as `re² + im²`, in order), and if
    `P > 0` every `w_i ← w_i + (μ/P)·e_n·conj(u_i)` (the factor `μ/P` computed once); without one,
    `e_n = 0` and the taps stay.
  The result has `symbols` (`y_n`) and `errors` (`e_n`), one each per output, and `taps` (`w` after
  the last output). With `μ = 0` the output is `x[n·sps]`. With `L = 1`, `μ = 1` and a reference,
  `y_{n+1}` uses the tap that makes `w·x[n·sps] = d_n` exactly, so a scalar channel `x = g·a` is
  inverted after one training symbol. **(implemented)**
- **RLS equalizer** (`rls_equalizer(samples, training, num_taps, forgetting, *, delta=0.01,
  samples_per_symbol=1, center=None, decision=None, initial_taps=None)`, [ADR
  0076](adr/0076-rls-equalizer.md)): exponentially weighted recursive least squares. `x`, `L`,
  `c`, `sps`, the start, the training, `decision`, the regressor `u` and the output
  `y_n = Σ_i w_i·u_i` are those of the LMS equalizer; the reference `d_n` is the training symbol
  for `n < T`, then the decision, else none. `λ = forgetting` is in `(0, 1]` and `δ = delta` is
  finite and above 0. `P` is an `L × L` complex matrix that starts at `I/δ`. For each output with
  a reference and `Σ_i |u_i|² > 0`, `e_n = d_n − y_n` and, every sum in order of its index:
  - `q_i = Σ_j P_ij·conj(u_j)`; `s = λ + Σ_i u_i·q_i`; `g_i = q_i / s`;
  - `w_i ← w_i + g_i·e_n`;
  - `r_j = Σ_i u_i·P_ij`; `P_ij ← (P_ij − g_i·r_j)/λ`.
  Otherwise nothing changes, and `e_n = 0` when there is no reference. The result is the LMS
  equalizer's: `symbols` (`y_n`), `errors` (`e_n`), `taps`. With `λ = 1` and every output
  trained, the taps after the last update are `(δI + Σ_k conj(u_k)·u_kᵀ)⁻¹(δ·w₀ + Σ_k
  conj(u_k)·d_k)`, `w₀` the start; with `λ < 1`, the same with `λ^{n−k}` on term `k` of `n`
  updates and `λⁿ` on both `δ` terms. **(implemented)**
- **Constant-modulus equalizer** (`cma_equalizer(samples, num_taps, step, *, samples_per_symbol=1,
  center=None, modulus=1.0, initial_taps=None)`, [ADR 0074](adr/0074-constant-modulus-equalizer.md)):
  blind, normalized. `x`, `L`, `c`, `sps`, `μ`, the start, the regressor `u` and the output
  `y_n = Σ_i w_i·u_i` are those of the LMS equalizer, with no training. `R = modulus` is finite and
  above 0. For every output `n = 0 … N − 1`: `e_n = y_n·(R − |y_n|²)`, with `|y_n|²` as
  `re² + im²`; `P = Σ_i |u_i|²` (in order), and if `P > 0` every `w_i ← w_i + (μ/P)·e_n·conj(u_i)`
  (the factor `μ/P` computed once). The result is the LMS equalizer's: `symbols` (`y_n`), `errors`
  (`e_n`), `taps`. With `L = 1`, input `x = g·a` with `|a| = 1` and `R = 1`, the tap after one
  update is `w·(1 + μ·(1 − |w·g|²))`. **(implemented)**
- **Decision-feedback equalizer** (`dfe_equalizer(samples, training, num_taps, num_feedback, step,
  *, samples_per_symbol=1, center=None, decision=None, initial_taps=None, initial_feedback=None,
  phase_loop_gains=None, pilots=None, pilot_interval=None, slip_window=2, forgetting=None,
  delta=0.01)`, [ADR 0069](adr/0069-decision-feedback-equalizer.md)): the LMS equalizer above with `M =
  num_feedback ≥ 0` feedback taps `b_1 … b_M`, all starting at 0 (or at `initial_feedback`, `M`
  finite values), on the past references
  `p_j = d_{n−j}` (0 for `n − j < 0`). With `M ≥ 1` every output needs a reference: `decision`
  given, or `T = N`. Each output:
  - `y_n = Σ_i w_i·u_i + Σ_j b_j·p_j`, the forward sum in order of `i`, then the feedback terms
    added in order of `j`;
  - `P = Σ_i |u_i|² + Σ_j |p_j|²` (forward then feedback, each in order, as `re² + im²`);
  - with `e_n = d_n − y_n` and `P > 0`, `w_i ← w_i + (μ/P)·e_n·conj(u_i)` and
    `b_j ← b_j + (μ/P)·e_n·conj(p_j)`;
  - the reference `d_n` then becomes `p_1` of the next output.
  The result has `symbols`, `errors`, `taps` (`w`) and `feedback_taps` (`b`, `M` of them). With
  `M = 0` it is `lms_equalizer` exactly. With `μ = 1` the updated taps give `d_n` exactly on the
  regressor they were updated on (the a posteriori error is 0).
  With `phase_loop_gains = [kp, ki]` (finite, `≥ 0`; [ADR 0073](adr/0073-equalizer-phase-loop.md))
  a second-order carrier loop turns the forward part, starting at `θ = 0`, `ν = 0`. Each output,
  with `r = cos θ − j·sin θ`:
  - `v = Σ_i w_i·u_i` (in order of `i`), and `y_n = v·r` with the feedback terms then added in
    order of `j`; `f = Σ_j b_j·p_j` (in order of `j`, before the update) is the feedback part;
  - the forward update uses `e_n·conj(r)` in place of `e_n` (the feedback update is unchanged);
  - with `q = d_n − f`, the phase error is `φ = atan2(Im c, Re c)` of `c = (v·r)·conj(q)`, or 0
    when `v` or `q` is 0; then `ν ← ν + ki·φ` and `θ ← θ + kp·φ + ν`.
  Without a reference there is no update and no loop step. With gains `[0, 0]` it is the
  equalizer without the loop exactly.
  With `pilot_interval = K ≥ 1` and `pilots` (both or neither; [ADR
  0075](adr/0075-pilot-slip-correction.md)), which need `phase_loop_gains` and `decision`: output
  `n ≥ T` is pilot `j = ⌊(n − T)/K⌋` when `(n − T) mod K = K − 1`, and `pilots` holds exactly
  `J = ⌊(N − T)/K⌋` finite symbols `g_0 … g_{J−1}`. `W = slip_window ≥ 1`; the step `σ` is `π/4`
  for `"psk8"` and `π/2` otherwise. At a pilot:
  - the reference is `d_n = g_j` in place of the decision;
  - after the loop step, `s ← s + y_n·conj(g_j)` (`s` starts at 0) and one more pilot is counted;
    when the count reaches `W`, `θ ← θ + k·σ` with `k` the integer nearest `atan2(Im s, Re s)/σ`
    (ties to even), and `s` and the count go back to 0.
  With `forgetting = λ` in `(0, 1]` (and `delta = δ`, finite and above 0; [ADR
  0077](adr/0077-rls-decision-feedback.md)) the tap update is RLS in place of LMS (`step` is
  checked but not used). The regressor is `z = (u_0·r, …, u_{L−1}·r, p_1, …, p_M)`, `K = L + M`
  values, with `r` as above (`z_i = u_i` without the loop), and the coefficients `θ = (w, b)`;
  `Q` (`K × K`) starts at `I/δ`. Where the LMS update would run (a reference and `P > 0`):
  `q_i = Σ_j Q_ij·conj(z_j)`, `s = λ + Σ_i z_i·q_i`, `g_i = q_i/s`, `θ_i ← θ_i + g_i·e_n`,
  `t_j = Σ_i z_i·Q_ij`, `Q_ij ← (Q_ij − g_i·t_j)/λ`, every sum in order of its index (as for
  `rls_equalizer`). The output, the loop step and the pilots are unchanged.
  **(implemented)**
- **Least-squares equalizer taps** (`dfe_least_squares(samples, training, num_taps, num_feedback,
  *, samples_per_symbol=1, center=None)` → `DfeTaps(taps, feedback_taps)`, [ADR
  0072](adr/0072-least-squares-equalizer-start.md)): the arguments as for `dfe_equalizer`, with
  `T ≥ L + M` and `T` at most the output count. For `n = 0 … T − 1` the regressor is
  `v_n = (u_0 … u_{L−1}, p_1 … p_M)`, `K = L + M` values: `u_i = x[n·sps + c − i]` (0 outside),
  `p_j = t_{n−j}` (0 for `n − j < 0`). The taps `θ = (w, b)` minimize `Σ_n |t_n − Σ_k θ_k·v_{n,k}|²`,
  the solution of `G·θ = h` with `G[k][l] = Σ_n conj(v_{n,k})·v_{n,l}` and `h[k] = Σ_n
  conj(v_{n,k})·t_n`, each summed in order of `n`. The solve, on copies:
  - for `k = 0 … K − 1`: the pivot row `r` is the first `r ≥ k` with the largest `|G[r][k]|²`
    (as `re² + im²`); if that is 0 the training does not determine the taps (`invalid_argument`);
    swap rows `r` and `k` of `G` and `h`; then for each `r > k` in order, `f = G[r][k]/G[k][k]`,
    `G[r][l] ← G[r][l] − f·G[k][l]` for `l = k + 1 … K − 1` and `h[r] ← h[r] − f·h[k]`;
  - for `k = K − 1` down to 0: `θ_k = (h[k] − Σ_{l=k+1}^{K−1} G[k][l]·θ_l)/G[k][k]`, the sum in
    order of `l` and subtracted from `h[k]` term by term.
  `taps` are `θ_0 … θ_{L−1}`, `feedback_taps` the rest. On a channel a finite DFE inverts exactly
  (no noise), the taps are the inverse: for `x_n = a_n + h·a_{n−1}` with `L = 1`, `M = 1`, `w = 1`
  and `b = −h`. **(implemented)**
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
  [15], `seed` [0], `modulation` [`"qpsk"`] (`"qpsk"`, `"qam16"`, `"psk8"`, `"qam64"`, `"fsk2"`,
  `"fsk4"` or `"ofdm"`, [ADR 0063](adr/0063-ofdm-link.md), [ADR 0051](adr/0051-psk8-link.md), [ADR 0053](adr/0053-qam64-link.md),
  [ADR 0057](adr/0057-fsk-link.md),
  [ADR 0050](adr/0050-link-modulation.md)), `phase_noise_linewidth_hz` [0] (`≥ 0`,
  [ADR 0047](adr/0047-link-phase-noise.md)), `clock_offset_ppm` [0] (`|·| ≤ 1e5`),
  `timing_loop_gains` [none] and
  `carrier_loop_gains` [none], each none or a pair `[kp, ki]` of numbers `≥ 0`
  ([ADR 0046](adr/0046-link-tracking-loops.md)), `ofdm_nfft` [64], `ofdm_cp_len` [16] and
  `ofdm_subcarriers` [none] (used by `"ofdm"` only, checked for every modulation as the OFDM
  bullet says), `multipath_delays` and `multipath_gains` [none] (both none or of equal non-zero
  length: integers `≥ 0`, and `[re, im]` pairs; `"ofdm"`, or a single-carrier chain with
  `equalizer_taps`, [ADR 0064](adr/0064-link-multipath.md)), `equalizer_taps` [none] (an integer
  `≥ 1`), `equalizer_step` [0.1] (in `[0, 2]`; [ADR 0067](adr/0067-link-equalizer.md)) and
  `equalizer_feedback` [0] (an integer `≥ 0`, nonzero only with `equalizer_taps`; [ADR
  0070](adr/0070-link-dfe-preamble-frequency.md)) and `equalizer_start` [`"impulse"`] (or
  `"least_squares"`; anything else only with `equalizer_taps`; [ADR
  0072](adr/0072-least-squares-equalizer-start.md)) and `equalizer_loop_gains` [none] (none or a
  pair `[kp, ki]` of numbers `≥ 0`, only with `equalizer_taps`; [ADR
  0073](adr/0073-equalizer-phase-loop.md)) and `pilot_interval` [none] (an integer `≥ 1`, only
  with `equalizer_loop_gains`; [ADR 0075](adr/0075-pilot-slip-correction.md)) and
  `equalizer_forgetting` [none] (a number in `(0, 1]`, only with `equalizer_taps`; [ADR
  0077](adr/0077-rls-decision-feedback.md)). Numbers must be finite.
  **(implemented)**
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
- **OFDM** (`"ofdm"`, [ADR 0063](adr/0063-ofdm-link.md), [0064](adr/0064-link-multipath.md),
  [0065](adr/0065-ofdm-phase-noise-clock.md)) replaces the transmitter and receiver
  below. `N = ofdm_nfft ≥ 2`, `cp = ofdm_cp_len` with `1 ≤ cp ≤ N`, `K = ofdm_subcarriers` (none:
  every index from `−⌊N/2⌋` to `N − 1 − ⌊N/2⌋` but 0; otherwise distinct integers in that range,
  at least one), `U = len(K)`. The checks above still apply and `rrc_taps(rolloff, sps,
  span_symbols)` must accept its arguments; `num_symbols` and `preamble_symbols` must be
  multiples of `U` (`B` and `P` blocks); `carrier_loop_gains` must be none,
  `|frequency_offset_hz| < fs/(2N)`, `fs = symbol_rate·sps`, and `|clock_offset_ppm|·10⁻⁶·
  (delay_samples + L) ≤ ⌊cp/2⌋ − D`, `D = max(multipath_delays)` or 0 without multipath.
  `rolloff`, `span_symbols` and `phase_block_symbols` are otherwise unused.
  - Transmitter: `bits = prbs(prbs_order, 2·num_symbols)`, `a = qpsk_map(bits)`, `tx` =
    `delay_samples` zeros, `ofdm_modulate(a, N, cp, K)` (`L = B·(N + cp)` samples) and `⌊cp/2⌋`
    zeros (room for every echo and a slow clock).
  - Channel: with multipath, `tx` first becomes `multipath(tx, multipath_delays, gains)` (each
    pair `[re, im]` as `re + j·im`), which needs `max(multipath_delays) ≤ ⌊cp/2⌋`; then as below, but the AWGN is `awgn(·, eb_n0_db + 10·log10 2, sps, signal_power =
    1/sps)`: variance `N₀ = 1/(2·10^(eb_n0_db/10))` per sample, so every used subcarrier sees
    `Es/N₀ = 2·Eb/N₀` (the prefix and empty subcarriers not counted).
  - Receiver:
    1. For each `d` in `0 … len(rx) − L`, `γ(d) = Σ_{b<B} Σ_{m<cp} r[d + b(N + cp) + m]·
       conj(r[d + b(N + cp) + m + N])` and `Φ(d)` the same sum of `(|r[i]|² + |r[i + N]|²)/2`;
       `d₀` is the first `d` maximizing `|γ(d)| − Φ(d)`, and
       `f̂ = −atan2(γ(d₀))·fs/(2πN)`. Then, with `x` the first `P·(N + cp)` samples of
       `ofdm_modulate(a, N, cp, K)`, `d₁` is the first `d` in `d₀ mod (N + cp)`,
       `+ (N + cp)`, …, `≤ len(rx) − L` maximizing `|Σ_i conj(x[i])·rx[d + i]·e^{−j2πf̂i/fs}|`
       (the prefix ties noiseless one block early when the delay is longer than a block). The
       steps below use `d₁` for `d₀`.
    2. Back off half a prefix: `d₂ = max(d₁ − ⌊cp/2⌋, 0)`, `s = d₁ − d₂`. `y =
       frequency_offset(rx[d₂ : d₂ + L], −f̂, fs, 2π·f̂·s/fs)` (phase 0 at `d₁`), `Z =
       ofdm_demodulate(y, N, cp, K)` as `B` rows of `U`, `A` the same of `a`.
    3. `G[b, k] = Z[b, k]/A[b, k]` for `b < P`; for `b ≥ 1`, with `t = Σ_k G[b, k]·conj(G[0, k])`,
       row `b` is multiplied by `conj(t)/|t|` (left as it is when `t = 0`), turning its common
       phase to block 0's. `Ĥ_k = (1/P)·Σ_{b<P} G[b, k]`, `W[b, k] = Z[b, k]/Ĥ_k`.
    4. Block by block, with `θ = τ = v = 0` before the first and `q(x) = qpsk_map(qpsk_demap(x))`:
       `R_k = W[b, k]·e^{−j(θ + 2πkτ/N)}`, the reference `Q_k = A[b, k]` for `b < P` (the known
       preamble) and `q(R_k)` after, `c = Σ_k R_k·conj(Q_k)`, `θ ← θ + atan2(c)`. With
       `timing_loop_gains [kp, ki]`, `φ_k = atan2(R_k·conj(Q_k)·conj(c))` (the residual phase
       about the common one), `e = (N/2π)·Σ_k (k − k̄)·φ_k / Σ_k (k − k̄)²` with `k̄` the mean of
       `K` (`e = 0` when `U = 1`), `v ← v + ki·e`, `τ ← τ + kp·e + v`; without, `τ` stays 0. Then
       `z[b, k] = W[b, k]·e^{−j(θ + 2πkτ/N)}`.
  - Report: `timing_offset = d₀ mod sps` (as a float), `frame_start = ⌊d₀/sps⌋`,
    `frequency_offset_hz = f̂`, `phase_offset = atan2(Σ_k Ĥ_k·e^{j2πk·s/N})` wrapped into
    `(−π, π]` (the window shift's ramp taken out),
    `evm = evm(z, a)`, `bit_errors(bits, qpsk_demap(z))` (the preamble counts), `ber_theory =
    qpsk_ber_theory(eb_n0_db)` or none without noise (exact channel knowledge; the estimate from
    `P` blocks costs roughly `10·log10(1 + 1/P)` dB). With multipath it is the mean over `k` in `K`
    of `qpsk_ber_theory(eb_n0_db + 10·log10|H_k|²)`, `1/2` where `H_k = 0`, with
    `H_k = Σᵢ gᵢ·e^{−j2πk·dᵢ/N}`. Phase noise and a clock offset do not change it (their
    leakage between subcarriers is not modeled). Noiseless and flat, `d₀ = delay_samples`, `f̂` is the
    channel offset to rounding, `phase_offset = phase + 2π·f·delay_samples/fs` wrapped, and there
    are no bit errors. **(implemented)**
- **Transmitter:** with `k` bits per symbol (2 for QPSK, 4 for 16-QAM, 3 for 8-PSK, 6 for
  64-QAM), `bits = prbs(prbs_order, k·num_symbols)`, `a = qpsk_map(bits)`, `qam16_map(bits)`,
  `psk8_map(bits)` or `qam64_map(bits)`,
  `h = rrc_taps(rolloff, sps, span_symbols)`, `tx` = `delay_samples` zeros followed by
  `pulse_shape(a, h, sps)`, and with multipath `max(multipath_delays)` zeros after that.
  **(implemented)**
- **Equalizer** ([ADR 0067](adr/0067-link-equalizer.md)): `equalizer_taps` is for the
  single-carrier chains only (FSK and `"ofdm"` reject it), needs an even `samples_per_symbol` and
  `preamble_symbols < num_symbols` (the preamble does not count, so something must be left), and
  rejects `timing_loop_gains` and `carrier_loop_gains`. Multipath in those chains needs it. With
  multipath the channel first makes `tx` `multipath(tx, multipath_delays, gains)`.
  **(implemented)**
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
     With `equalizer_taps` and `P ≥ 2`, `f₁` is instead data-aided, for every modulation: with
     `d[i] = r[i+1]·conj(r[i])` and `e[i] = a[i+1]·conj(a[i])`, `D(k) = Σ_{i=0}^{P−2}
     conj(e[i])·d[k+i]` for `k = 0 … len(r) − N`, `k₁` the first `k` with the
     largest `|D(k)|`, and `f₁ = arg(D(k₁))·symbol_rate/(2π)`
     ([ADR 0071](adr/0071-link-data-aided-coarse-frequency.md)). `k₁` sets only `f₁`.
  3. Frame start `k₀`: the first `k` in `0 … len(r) − N` that maximizes
     `q(k) = Σ_b |Σ_{i=bB}^{min((b+1)B, P)−1} conj(a[i])·c[k+i]|`, over the blocks
     `b = 0 … ⌈P/B⌉ − 1` of the preamble ([ADR 0068](adr/0068-block-frame-search.md): a residual
     frequency error turns a long coherent sum through a cycle). With `P ≤ B` it is the one
     coherent sum `|Σ_{i<P} conj(a[i])·c[k+i]|`.
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
     With `equalizer_taps = L` they are instead `dfe_equalizer(x, a[:P], L, M, equalizer_step,
     samples_per_symbol=2, decision=modulation).symbols` with `M = equalizer_feedback` (`M = 0`
     is `lms_equalizer`); with `equalizer_start = "least_squares"` it also passes the
     `dfe_least_squares(x, a[:P], L, M, samples_per_symbol=2)` taps as `initial_taps` and
     `initial_feedback` (`P ≥ L + M` is then needed), `equalizer_loop_gains` as
     `phase_loop_gains`, `equalizer_forgetting` as `forgetting`, and with `pilot_interval = K` that as `pilot_interval` with `pilots` the
     symbols `a[P + (j + 1)·K − 1]`, `j < ⌊(N − P)/K⌋`, where `v = frequency_offset(y, −f, symbol_rate·sps)`, `s₀ = (round(τ) mod sps) + k₀·sps`, and `x` the `2N` samples
     `x[m] = v[s₀ + m·sps/2]`, 0 past the end of `v`. Output `n` then starts as `v[s₀ + n·sps]`,
     the sample the steps above take. With the equalizer the preamble does not count: `evm` and
     `bit_errors` compare symbols `P … N − 1` only (the bits from `k·P` on), and with pilots
     not those at the pilots either (nor their `k` bits each). With the equalizer
     and `n_b = ⌊P/B⌋ ≥ 2`, `f` here (and as reported) is instead the preamble's: `q_b =
     Σ_{i=bB}^{(b+1)B−1} conj(a[i])·c[k₀+i]` for `b < n_b`, each summed in order of `i`; their
     phases unwrapped as `θ₀ = arg q₀`, `θ_b = θ_{b−1} + arg(q_b·conj(q_{b−1}))`; `s` the
     least-squares slope of `θ_b` on `x_b = b·B` (step 5's formula); and `f = f₁ +
     s·symbol_rate/(2π)` ([ADR 0070](adr/0070-link-dfe-preamble-frequency.md)).
  **(implemented)**
- **Report** (`QpskLinkReport`): `config`, `timing_offset` (τ, samples; the loop's start when it
  runs), `frame_start` (`k₀`,
  symbols into `r`), `frequency_offset_hz` (`f`), `phase_offset` (`φ`, rad: the carrier phase at the
  frame's first symbol), `evm` (an EVM record), `bit_errors` (an error-count record), `ber_theory`
  (`qpsk_ber_theory`, `qam16_ber_theory`, `psk8_ber_theory` or `qam64_ber_theory` of
  `eb_n0_db`, or none without noise). With multipath it is the matched-filter bound, that theory
  at `eb_n0_db + 10·log10 E_h` (`1/2` if `E_h = 0`), `E_h = Σᵢ Σⱼ gᵢ·conj(gⱼ)·ρ((dⱼ − dᵢ)/sps)`
  over the paths (its real part, summed in order of `i` then `j`), `ρ(t) = sinc(t)·cos(πβt)/(1 −
  (2βt)²)` the raised cosine of `β = rolloff` (`(π/4)·sinc(1/(2β))` where `|t| = 1/(2β)`,
  `sinc(t) = sin(πt)/(πt)`, `sinc(0) = 1`). It is a lower bound on the BER, not a
  prediction. For FSK see above: `frequency_offset_hz`, `phase_offset`
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
  `r` (real); type `f64`, `f32`, `f16` ([ADR 0087](adr/0087-half-float-samples.md)), `i32`, `i16`,
  `i8`, `u32`, `u16` or `u8` (unsigned: [ADR 0058](adr/0058-unsigned-sample-types.md)); order `le`
  or `be`, which `i8` and `u8` omit and every other type requires. Anything else (`i64`, a missing
  or extra order) is rejected. **(implemented)**
- **Integer scaling**: code `c` of a `b`-bit type is the sample `c / 2^(b−1)`, so full scale is
  1.0 (units `"FS"` if the caller wants to say so). Writing, a sample becomes
  `round(x·2^(b−1))`, rounding half to even; a non-finite sample or a code outside
  `−2^(b−1) … 2^(b−1) − 1` is rejected (nothing is clipped silently, so `+1.0` itself cannot be
  written). Complex samples scale each part. Unsigned types are offset binary: code `u` is the
  sample `(u − 2^(b−1)) / 2^(b−1)`, and writing gives `round(x·2^(b−1)) + 2^(b−1)` (half to even),
  rejected outside `0 … 2^b − 1`: the signed code with its top bit flipped, so the same range and
  step as the signed type. **(implemented)**
- **Floats** are stored as IEEE binary64, binary32 or binary16 in the given byte order; writing
  `f32` or `f16` rounds once from the binary64 value to nearest even (`f16` never goes through
  binary32), and a value beyond the range becomes ±inf (`f16`: 65520 and up). Subnormals are kept.
  NaN and ±inf are stored as they are.
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
  integer 1 (see **Channels**), `core:dataset` or `core:metadata_only`, a capture whose
  `core:header_bytes` is not the integer 0, captures with
  different `core:frequency` (a missing one is 0), a data file that is not a whole number of
  samples, JSON with duplicate keys or the non-standard `NaN`/`Infinity`, `annotations: null`, and
  a global field named `core:annotations`. Other global fields go to `metadata` under their own
  names; the rest of each capture is not read.
  JSON numbers without a fraction or exponent are integers (`int` / `long`), others floats;
  writing, a float always gets a fraction or an exponent (`2.0`, not `2`), so the kind survives a
  trip through the other language. `captures` and `signalforge:metadata` may be missing, but `null`
  is not an array or an object and is rejected. A missing or unreadable file is an OS error
  (`OSError` / `IOException`), not `invalid_argument`. **(implemented)**
- **Channels** ([ADR 0096](adr/0096-sigmf-channels.md)): `read_sigmf_channels(path)` and
  `write_sigmf_channels(path, channels, datatype)` (C# `ReadSigmfChannels`, `WriteSigmfChannels`)
  read and write a list of signals, one per channel; `read_sigmf` still takes one channel only.
  `core:num_channels` is a JSON integer from 1 to 65535 (`MAX_CHANNELS` /
  `SignalFiles.MaxChannels`), missing meaning 1. Sample `k` of channel `c` is sample `k·N + c`
  of the data; the data must be a whole number of `N`-sample frames. Every channel gets the
  recording's rate, center frequency, time origin, units, impedance and metadata (its own copy,
  annotations included). Writing: a non-empty list of at most 65535 signals of one kind and one
  length, whose metadata files as `write_sigmf` would write them are identical (so those fields
  agree exactly; `1` and `1.0` differ); `core:num_channels` follows `core:sample_rate` when there
  is more than one channel, and one channel gives the `write_sigmf` files. **(implemented)**
- **Captures** ([ADR 0097](adr/0097-sigmf-captures.md)): `read_sigmf_captures(path)` (C#
  `ReadSigmfCaptures`) reads a one-channel recording as one signal per capture, in file order;
  `read_sigmf` still rejects captures at different frequencies. Each capture needs
  `core:sample_start`, a JSON integer; the first is 0, each is greater than the last, none is
  past the number of samples. Capture `j` holds samples `start_j` up to the next start (the last,
  to the end); no captures is one segment at frequency 0. A segment's center frequency is its
  capture's `core:frequency` (missing: 0) and its time origin `time_origin + start_j /
  sample_rate`; other capture fields are not read. Rate, units, impedance and metadata are the
  recording's (each its own copy). An annotation goes to the last segment starting at or before
  its `core:sample_start`, which becomes `core:sample_start − start_j`; its other fields are
  kept, and a span past its segment is not checked. **(implemented)**
  Writing ([ADR 0100](adr/0100-sigmf-write-captures.md)): `write_sigmf_captures(path, segments,
  datatype=None)` (C# `WriteSigmfCaptures`) joins a non-empty list of signals of one kind.
  Segment `j` starts at `start_j`, the sum of the earlier lengths, and gives the capture
  `{"core:sample_start": start_j, "core:frequency": f_j}`. Each later time origin must be exactly
  `t₀ + start_j / sample_rate`. The `global` objects `write_sigmf` would write, apart from the time
  origin, must be identical. Only the last segment may be empty. Annotations move up by `start_j`.
  In every segment but the last, each must start before the segment's end. One segment gives the
  `write_sigmf` files. **(implemented)**
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
  - Text tags ([ADR 0091](adr/0091-wav-info.md)): `write_wav(..., info=None)` and
    `read_wav_info(path)` (C# `WriteWav(..., info)`, `ReadWavInfo`). Writing a non-empty `info`
    adds, after `data` and its pad, `LIST`, the size of the rest, `INFO`, then for each tag in
    order its ID, the size of the text plus one, the text, a NUL, and a zero pad byte when that
    size is odd; the RIFF size counts it all. An ID is four characters from `A`–`Z` and `0`–`9`,
    each used once; a text is printable ASCII (`0x20`–`0x7E`), possibly empty. No or empty `info`
    writes no `LIST` chunk. Reading needs `RIFF` and `WAVE`, then walks every chunk to the end of
    the file (not stopping at `data`), reading each `LIST` whose body starts with `INFO`, in file
    order, as an ordered mapping of ID to text. Subchunks are an ID, a 32-bit size and a body
    padded to even. A text is its body up to the first NUL (all of it without one); IDs and texts
    are decoded byte for byte as Latin-1. Rejected: a chunk running past the end of the file, a
    subchunk running past its `LIST`, and an ID seen twice anywhere in the file. A walk (of the
    file or of a `LIST` body) ends when fewer than 8 bytes are left, and those bytes are ignored;
    so a missing pad byte after the last chunk or subchunk is allowed. **(implemented)**
  - Cue points ([ADR 0094](adr/0094-wav-cues.md)): `write_wav(..., cues=None)` and
    `read_wav_cues(path)` (C# `WriteWav(..., cues)`, `ReadWavCues`), each cue a (position,
    length, label) triple (the length below), the position in sample frames from the start of
    the data. Writing a non-empty
    `cues` adds, after `data` and its pad and before any `LIST`/`INFO`: `cue `, the size
    4 + 24k, the count k, then per point its ID (1, 2, … in order), the position, `data`, 0, 0,
    and the position again; then, if any label is non-empty, `LIST`, its size, `adtl`, and per
    non-empty label `labl`, the size 4 + text length + 1, the cue ID, the text, a NUL and a pad
    byte when that size is odd. A position is a whole number from 0 to the samples per channel; a
    label is printable ASCII, possibly empty. Reading walks the chunks as `read_wav_info` does and
    needs a `fmt ` of at least 16 bytes with a non-zero block align (bytes 12–13) and a `data`
    chunk; frames = data size ÷ block align, rounded down. At most one `cue `, of size exactly
    4 + 24 × count; each point must name `data` with chunk start and block start 0, its sample
    offset (last field) is the position and must be at most the frames, and its ID must be new;
    the play-order field is ignored. Each `labl` in a `LIST`/`adtl` needs at least 4 bytes; its
    text runs from byte 4 to the first NUL, as Latin-1, and its ID must name a cue point that has
    no label yet. Other `adtl` subchunks are skipped. Points come back in the `cue ` chunk's
    order, a point without a label with `""`; no `cue ` chunk means no cues. **(implemented)**
  - Cue regions ([ADR 0095](adr/0095-wav-cue-regions.md)): a cue is (position, length, label),
    length 0 for a plain point, in reading and writing alike. A length is a whole number with
    position + length at most the frames. Writing puts the `LIST`/`adtl` chunk out when any cue
    has a label or a length, and per cue in order its `labl` (non-empty label) then its `ltxt`
    (non-zero length): `ltxt`, size 20, the cue ID, the length, `rgn `, and four 16-bit zeros
    (country, language, dialect, code page). Reading takes each `ltxt` of at least 20 bytes: bytes
    0–3 the cue ID, which must name a cue point with no `ltxt` yet, bytes 4–7 the length; the
    rest is ignored. Position + length must be at most the frames. No `ltxt` means length 0.
    **(implemented)**
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
    value) and `shape`, each once. The descr is `'<f8'`, `'>f8'`, `'<f4'`, `'>f4'`, `'<f2'`,
    `'>f2'`, `'<c16'`, `'>c16'`, `'<c8'` or `'>c8'` ([ADR 0088](adr/0088-npy-read-dtypes.md)):
    IEEE binary64, binary32 or binary16 in that byte order, a complex item being the real then
    the imaginary part. Values are widened exactly to `float64` / `complex128`; a NaN stays NaN.
    The descr may also be an integer one ([ADR 0090](adr/0090-npy-integer-dtypes.md)): `'|i1'`,
    `'|u1'`, or `<` or `>` with `i2`, `u2`, `i4`, `u4`, `i8` or `u8`, two's-complement signed or
    unsigned in that byte order. Each integer becomes the real `float64` of the same value, with
    no scaling; a 64-bit value beyond 2^53 in magnitude rounds to the nearest double, ties to even.
    Rejected: anything else, any other descr (`=` byte order, `|` on a float or a multi-byte
    integer, `<` or `>` on a one-byte integer, booleans, structured), a shape that is not one
    integer, and a data size other than `n` × the item size.
    In C# a file of the other kind than `T` is rejected (an integer file is real). A missing file is an OS error.
    **(implemented)**
  - 2-D arrays ([ADR 0092](adr/0092-npy-2d.md)): `read_npy_2d(path)` (C# `ReadNpy2D<T>`, a `T[,]`)
    reads what `read_npy` reads except that the shape is exactly two integers `(r, c)`, each at
    most 2147483591 (2^31 − 57), and the data is `r × c` items. Item `k` of the data is row `k ÷ c`, column
    `k mod c` when `fortran_order` is `False`, and row `k mod r`, column `k ÷ r` when it is `True`;
    the result is in C order either way. Zero rows or columns mean no data. `read_npy` rejects a
    2-D shape and `read_npy_2d` a 1-D one. `write_npy` of a 2-D array writes the header text
    `{'descr': '<f8', 'fortran_order': False, 'shape': (r, c), }` (`'<c16'` for complex), padded
    as above to 118 bytes, then the items in C order (row by row). `.npz` members may be 2-D too
    (ADR 0093). **(implemented)**
- **NumPy `.npz`** ([ADR 0089](adr/0089-npz.md)): `write_npz(path, arrays)`, `read_npz(path)` (C#
  `WriteNpz`, `ReadNpz`), a ZIP archive of one `.npy` member per array, named `<key>.npy`, in the
  mapping's order. All numbers in the ZIP structures are little-endian.
  - Writing: for each member, a local header (`50 4B 03 04`, version needed 20, flags 0, method
    0, time 0, date `0x0021`, CRC-32, size, size, name length, extra length 0, the name), then the
    member's `write_npy` bytes. Then one central header per member (`50 4B 01 02`, version made by
    20, version needed 20, flags 0, method 0, time 0, date `0x0021`, CRC-32, size, size, name
    length, extra 0, comment 0, disk 0, internal attributes 0, external attributes 0, the local
    header's offset, the name). Then the end record (`50 4B 05 06`, disks 0 and 0, the member
    count twice, the central directory's size and offset, comment length 0). CRC-32 is the ZIP
    one: reflected polynomial `0xEDB88320`, initial value and final XOR `0xFFFFFFFF`. Keys are 1
    to 250 printable ASCII characters without `/` or `\`, each used once; at most 65535 members,
    and the archive must stay under 4 GiB. An empty mapping writes just the end record. A
    member may be 1-D or 2-D ([ADR 0093](adr/0093-npz-2d.md)); each is written with the bytes
    `write_npy` writes for it.
  - Reading: the end record is the last `50 4B 05 06` that sits within 65557 bytes of the end and
    whose comment runs exactly to the end. Its disk numbers must be 0, and its two counts must be
    equal. An archive that needs ZIP64 (a count of `0xFFFF`, or a size or offset of `0xFFFFFFFF`,
    in the end record) is rejected. The central directory must lie inside the file and hold
    exactly the count of headers. For each central header:
    - flag bit 0 (encryption) is rejected;
    - the method must be 0 or 8;
    - a compressed size, an uncompressed size or an offset of `0xFFFFFFFF` is taken from the ZIP64
      extra field (`0x0001`), whose 8-byte values come in that order and only for the fields that
      are `0xFFFFFFFF`;
    - the name is UTF-8 if flag bit 11 is set, otherwise ASCII;
    - the name must end in `.npy`, and the key (the name without it) must be non-empty and
      unique.

    At the offset there must be a local header (`50 4B 03 04`); the data starts after its name and
    extra field (their lengths are the local header's own). Stored data must have the
    uncompressed size. Deflated data must inflate to exactly the uncompressed size (bytes after the
    end of the deflate stream are not checked: .NET's inflater cannot report them). The CRC-32 of the result must match. The result is then read as a
    `.npy` file: a 1-D member as `read_npy` reads it, a 2-D one as `read_npy_2d` does (ADR 0093),
    and any other shape is rejected. Anything else is `invalid_argument`. A missing file is an OS
    error.
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
