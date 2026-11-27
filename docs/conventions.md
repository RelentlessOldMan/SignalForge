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
- Python arrays of real numbers (ADR 0621) take integer, unsigned and floating dtypes, or object
  arrays of real numbers that are not bools and fit in a double. Bool, string, bytes, date and time arrays are refused. Arrays of samples that may be complex
  (`Signal`, `iq_imbalance`; ADR 0622) take the same, plus complex dtypes and complex objects.
  **(implemented)**
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
- **FM tone** (`fm_tone(sample_rate, num_samples, carrier, modulator, index, amplitude=1)`,
  C# `Waveforms.FmTone`, [ADR 0306](adr/0306-fm-tone.md)): real,
  `A·cos(2π·fc·(n/fs) + I·sin(2π·fm·(n/fs)))`, `2π·f` formed first as in `tone`. Positive
  finite `sample_rate`; `carrier`, `modulator`, `index`, `amplitude` finite. **(implemented)**
- **Pulse-width modulation** (`pwm(duty, sample_rate, frequency, amplitude=1, phase=0)`, C#
  `Waveforms.Pwm`, [ADR 0312](adr/0312-pwm.md)): one sample per `duty` value; `u[n]` as for the
  oscillators; `y[n] = A` for `u[n] < duty[n]`, else `−A`. `duty` a 1-D real array (may be
  empty), every value in [0, 1]; positive finite `sample_rate`; finite `frequency`,
  `amplitude`, `phase`. **(implemented)**
- **Feedback FM operator** (`feedback_fm(sample_rate, num_samples, frequency, feedback,
  amplitude=1, phase=0)`, C# `Waveforms.FeedbackFm`, [ADR 0322](adr/0322-feedback-fm.md)): `u`
  as for the oscillators; `s[−1] = 0`, `s[n] = sin((2π·u[n]) + (feedback·s[n−1]))`; `y = A·s`.
  Finite `frequency`, `amplitude`, `phase`; finite `0 ≤ feedback ≤ 1.5`. **(implemented)**
- **Bandlimited impulse train** (`blit(sample_rate, num_samples, frequency, amplitude=1,
  phase=0)`, C# `Waveforms.Blit`, [ADR 0320](adr/0320-blit.md)): `H` the number of `m ≥ 1`
  with `m·|f| < fs/2` (`⌊fs/(2|f|)⌋`, less 1 when `H·|f| ≥ fs/2`), `M = 2H + 1`;
  `y = A·(1 + 2·Σ_{m=1}^{H} cos(2π·m·u))/M`, computed with `v = u` (`u ≤ 1/2`) or `u − 1` as
  `A` at `v = 0`, else `A·(sin(M·(π·v))/(M·sin(π·v)))`. Finite non-zero `frequency`,
  `|f| ≤ fs/2`; finite `amplitude`, `phase`. **(implemented)**
- **Phase-distortion oscillator** (`phase_distortion(sample_rate, num_samples, frequency, knee,
  amplitude=1, phase=0)`, C# `Waveforms.PhaseDistortion`,
  [ADR 0319](adr/0319-phase-distortion.md)): `u` as for the oscillators; `w = u/(2·knee)` for
  `u < knee`, else `1/2 + (u − knee)/(2·(1 − knee))`; `y = −A·cos(2π·w)`. Finite `frequency`,
  `amplitude`, `phase`; finite `0 < knee < 1`. **(implemented)**
- **DPW sawtooth** (`dpw_sawtooth(sample_rate, num_samples, frequency, amplitude=1,
  phase=0)`, C# `Waveforms.DpwSawtooth`, [ADR 0317](adr/0317-dpw-sawtooth.md)): `u[n]` as for
  the oscillators, also at `n = −1`; `x = 2·u − 1`;
  `y[n] = A·((x[n]·x[n] − x[n−1]·x[n−1])·(fs/(4·f)))`; at `f = 0`, `y = A·x`. Rules of the
  PolyBLEP sawtooth. **(implemented)**
- **Supersaw** (`supersaw(sample_rate, num_samples, frequency, detune, voices=7,
  amplitude=1)`, C# `Waveforms.Supersaw`, [ADR 0316](adr/0316-supersaw.md)): voice `k` of `V`
  at `c_k = detune·(2·k/(V − 1) − 1)` cents (0 when `V = 1`), `f_k = f·2^(c_k/1200)`, the
  PolyBLEP sawtooth at `f_k`, amplitude 1, phase `k/V`; `y = A·(Σ_k voice_k)/V`, summed in order
  of `k`. Finite `frequency`, `amplitude`; finite `detune ≥ 0`; integer `voices ≥ 1`; every
  `|f_k| ≤ fs/2`. **(implemented)**
- **Hard-synced sawtooth** (`hard_sync_sawtooth(sample_rate, num_samples, frequency,
  sync_frequency, amplitude=1)`, C# `Waveforms.HardSyncSawtooth`,
  [ADR 0315](adr/0315-hard-sync-sawtooth.md)): `m = frac(sync_frequency·(n/fs))`;
  `u = frac((frequency / sync_frequency)·m)`; `y = A·(2·u − 1)`. Positive finite
  `sample_rate` and `sync_frequency`; finite `frequency`, `amplitude`. **(implemented)**
- **PolyBLEP triangle** (`polyblep_triangle(sample_rate, num_samples, frequency,
  amplitude=1, phase=0)`, C# `Waveforms.PolyblepTriangle`,
  [ADR 0314](adr/0314-polyblep-triangle.md)): `u`, `dt` as for the PolyBLEP sawtooth;
  `E(x) = w·w·w/6`, `w = 1 − x`, for `x < 1`; `d₀ = min(u, 1 − u)`, `d₁ = |u − 1/2|`;
  `c = −E(d₀/dt)` if `d₀ < dt`, then `+ E(d₁/dt)` if `d₁ < dt`;
  `y = A·((4·|u − 1/2| − 1) + 8·dt·c)`. Rules of the PolyBLEP sawtooth. **(implemented)**
- **PolyBLEP pulse-width modulation** (`polyblep_pwm(duty, sample_rate, frequency,
  amplitude=1, phase=0)`, C# `Waveforms.PolyblepPwm`, [ADR 0313](adr/0313-polyblep-pwm.md)):
  the PolyBLEP square's rule with `duty = duty[n]` at sample `n`; one sample per `duty` value.
  Rules of `pwm`, and `|f| ≤ fs/2`. **(implemented)**
- **PolyBLEP square** (`polyblep_square(sample_rate, num_samples, frequency, duty=0.5,
  amplitude=1, phase=0)`, C# `Waveforms.PolyblepSquare`,
  [ADR 0311](adr/0311-polyblep-square.md)): `u` and `dt` as for the PolyBLEP sawtooth, `r(·)`
  its residual; `v = u − duty`, plus 1 when `u < duty`; `y = s + A·r(u) − A·r(v)` with `s` the
  naive square (`A` for `u < duty`, else `−A`). Rules of the square, and `|f| ≤ fs/2`.
  **(implemented)**
- **PolyBLEP sawtooth** (`polyblep_sawtooth(sample_rate, num_samples, frequency,
  amplitude=1, phase=0)`, C# `Waveforms.PolyblepSawtooth`,
  [ADR 0310](adr/0310-polyblep-sawtooth.md)): `u` as for the oscillators, `dt = |f|/fs`; for
  `u < dt`, `t = u/dt`, `r = t + t − t·t − 1`; else for `u > 1 − dt`, `t = (u − 1)/dt`,
  `r = t·t + t + t + 1`; else `r = 0`; `y = A·((2·u − 1) − r)`. Positive finite
  `sample_rate`; finite `frequency` with `|f| ≤ fs/2`; finite `amplitude`, `phase`.
  **(implemented)**
- **Band-limited square and triangle** (`bandlimited_square(...)`,
  `bandlimited_triangle(...)`, same arguments as `bandlimited_sawtooth`, C#
  `Waveforms.BandlimitedSquare`, `BandlimitedTriangle`,
  [ADR 0309](adr/0309-bandlimited-square-triangle.md)): `u` and `K` as for the band-limited
  sawtooth; sums over odd `k ≤ K` in increasing order; square `((4·A)/π)·Σ sin((2π·k)·u)/k`;
  triangle `((8·A)/(π·π))·Σ cos((2π·k)·u)/(k·k)`. Same rules as the sawtooth.
  **(implemented)**
- **Band-limited sawtooth** (`bandlimited_sawtooth(sample_rate, num_samples, frequency,
  amplitude=1, phase=0)`, C# `Waveforms.BandlimitedSawtooth`,
  [ADR 0307](adr/0307-bandlimited-sawtooth.md)): `u` as for the oscillators; `K` the largest
  `k ≥ 0` with `k·|f| < fs/2` in floating point; `S = Σ_{k=1..K} sin((2π·k)·u)/k` from `k = 1`
  up; `y = ((−2·A)/π)·S`. Positive finite `sample_rate`; finite, non-zero `frequency`; finite
  `amplitude`, `phase`. **(implemented)**
- **Wavetable oscillator** (`wavetable(table, sample_rate, num_samples, frequency, phase=0)`,
  C# `Waveforms.Wavetable`, [ADR 0308](adr/0308-wavetable.md)): `u` as for the oscillators;
  `p = u·L`, `i = floor(p)` (taken as `i − L` if it reaches `L`), `r = p − i`;
  `y = T[i]·(1 − r) + T[(i + 1) mod L]·r`. Real, finite table of at least one entry; positive
  finite `sample_rate`; finite `frequency`, `phase`. **(implemented)**
- **Oscillators** (`sawtooth(sample_rate, num_samples, frequency, amplitude=1, phase=0)`,
  `square(…, frequency, duty=0.5, amplitude=1, phase=0)`, `triangle(…)`, C#
  `Waveforms.Sawtooth`, `Square`, `Triangle`, [ADR 0305](adr/0305-oscillators.md)): real;
  `phase` in **cycles**; `t = f·(n/fs) + phase`, `u = t − floor(t)`; sawtooth `A·(2u − 1)`;
  square `A` for `u < duty`, else `−A`; triangle `A·(4·|u − 1/2| − 1)`. Naive (they alias).
  Positive finite `sample_rate`; finite `frequency`, `amplitude`, `phase`; `duty` in [0, 1].
  **(implemented)**
- **ADSR envelope** (`adsr(num_samples, attack, decay, sustain, release, gate)`, C#
  `Waveforms.Adsr`, [ADR 0303](adr/0303-adsr.md)): held, `h(n) = n/A` for `n < A`,
  `1 − (1 − S)·((n − A)/D)` for `A ≤ n < A + D`, `S` after; for `n ≥ G`, `k = n − G`,
  `h(G)·(1 − k/R)` for `k < R` and 0 after. Integer counts at least 0 (`num_samples` at least
  1); `sustain` in [0, 1]. **(implemented)**
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
- **Allan deviation** ([ADR 0327](adr/0327-allan-deviation.md);
  `allan_deviation(fractional_frequency, sample_interval, averaging_factors)`, C#
  `Measurements.AllanDeviation`): overlapping; per factor `m`, `ȳ_k` the direct mean of
  `y[k … k+m−1]`, `σ² = Σ_{j=0}^{M−2m} (ȳ_{j+m} − ȳ_j)² / (2(M − 2m + 1))`, `τ = m·τ₀`. Gives
  `AllanDeviation(taus, deviations)` in the factors' order. Real, finite, `M ≥ 2`; finite
  positive `sample_interval`; non-empty integer factors with `1 ≤ m` and `2m ≤ M`.
  **(implemented)**
- **Modified Allan deviation** ([ADR 0328](adr/0328-modified-allan-deviation.md);
  `modified_allan_deviation(fractional_frequency, sample_interval, averaging_factors)`, C#
  `Measurements.ModifiedAllanDeviation`): `ȳ_k` as for the Allan deviation, `d_i = ȳ_{i+m} −
  ȳ_i`, `S_j = Σ_{i=j}^{j+m−1} d_i` for `j = 0 … M−3m+1`, `σ² = Σ S_j² / (2m²(M − 3m + 2))`,
  `τ = m·τ₀`. Gives `AllanDeviation(taus, deviations)`. Rules as the Allan deviation but
  `3m ≤ M + 1`. **(implemented)**
- **Hadamard deviation** ([ADR 0329](adr/0329-hadamard-deviation.md);
  `hadamard_deviation(fractional_frequency, sample_interval, averaging_factors)`, C#
  `Measurements.HadamardDeviation`): overlapping; `ȳ_k` as for the Allan deviation,
  `σ² = Σ_{j=0}^{M−3m} ((ȳ_{j+2m} − ȳ_{j+m}) − (ȳ_{j+m} − ȳ_j))² / (6(M − 3m + 1))`,
  `τ = m·τ₀`. Gives `AllanDeviation(taus, deviations)`. Rules as the Allan deviation but
  `3m ≤ M`. **(implemented)**
- **Higuchi fractal dimension** ([ADR 0330](adr/0330-higuchi-dimension.md);
  `higuchi_dimension(samples, k_max)`, C# `Measurements.HiguchiDimension`): for `k = 1 … k_max`,
  starts `m < k`, `n_m = floor((N−1−m)/k)`, `L_m(k) = Σ_{i=1}^{n_m} |x[m+ik] − x[m+(i−1)k]| ·
  (N−1)/(n_m k) / k`, `L(k)` their mean; the least-squares slope of `ln L(k)` against `−ln k`.
  Real, finite; integer `k_max ≥ 2` with `2·k_max ≤ N`; every `L(k) > 0`. **(implemented)**
- **Time deviation** ([ADR 0331](adr/0331-time-deviation.md);
  `time_deviation(fractional_frequency, sample_interval, averaging_factors)`, C#
  `Measurements.TimeDeviation`): `TDEV = (τ/√3)·MDEV(τ)` in seconds, MDEV as the modified Allan
  deviation; the same rules and result type. **(implemented)**
- **Detrended fluctuation analysis** ([ADR 0332](adr/0332-detrended-fluctuation.md);
  `detrended_fluctuation(samples, scales)`, C# `Measurements.DetrendedFluctuation`): DFA-1. Profile
  `Y[i] = Σ_{j≤i} (x[j] − x̄)`; for scale `s`, `B = floor(N/s)` boxes from the start, a
  least-squares line over `t = 0 … s−1` removed in each; `F(s) = sqrt(Σ r² / (B·s))`; `α` the
  least-squares slope of `ln F` against `ln s`. Result `(scales, fluctuations, alpha)`. Real,
  finite; at least two strictly increasing integer scales, `4 ≤ s ≤ N`; every `F(s) > 0`.
  **(implemented)**
- **Approximate entropy** ([ADR 0333](adr/0333-approximate-entropy.md);
  `approximate_entropy(samples, m, r)`, C# `Measurements.ApproximateEntropy`): Pincus's
  `Φ_m − Φ_{m+1}`, `Φ_k = (1/n_k) Σ_i ln C_i^k`, `n_k = N − k + 1` templates, `C_i^k` the share
  of templates (self included) within `r` by the Chebyshev distance. Real, finite, at least
  `m + 2` samples; integer `m ≥ 1`; finite `r ≥ 0` in sample units. **(implemented)**
- **Katz fractal dimension** ([ADR 0334](adr/0334-katz-dimension.md); `katz_dimension(samples)`,
  C# `Measurements.KatzDimension`): points `(i, x[i])`; `n = N − 1` steps,
  `L = Σ sqrt(1 + Δx²)`, `d = max_i sqrt(i² + (x[i] − x[0])²)`,
  `D = log10 n / (log10 n + log10(d/L))`. Real, finite, at least 3 samples; the denominator must
  be above 0. **(implemented)**
- **Petrosian fractal dimension** ([ADR 0335](adr/0335-petrosian-dimension.md);
  `petrosian_dimension(samples)`, C# `Measurements.PetrosianDimension`): `n = N`, `N_Δ` the `i`
  with `sign(Δ[i])·sign(Δ[i+1]) < 0`, `D = log10 n / (log10 n + log10(n/(n + 0.4 N_Δ)))`. Real,
  finite, at least 3 samples. **(implemented)**
- **Lempel-Ziv complexity** ([ADR 0336](adr/0336-lempel-ziv-complexity.md);
  `lempel_ziv_complexity(bits)`, C# `Measurements.LempelZivComplexity`): the LZ76 phrase count;
  each phrase `s[p … q]` has the smallest `q` with `s[p … q]` not a substring of `s[0 … q−1]`; a
  copyable piece at the end counts as one. Bits 0 or 1, at least one; raw count, not normalized.
  **(implemented)**
- **Maximum time interval error** ([ADR 0337](adr/0337-mtie.md); `mtie(time_error,
  sample_interval, window_sizes)`, C# `Measurements.Mtie`): time-error samples in seconds; for
  each `n`, `τ = n·τ₀` and `MTIE = max_k (max − min of x[k … k+n])`. Result `(taus, values)`.
  Real, finite, at least 2 samples; finite positive `τ₀`; window sizes not empty,
  `1 ≤ n ≤ N − 1`. **(implemented)**
- **Multiscale entropy** ([ADR 0338](adr/0338-multiscale-entropy.md);
  `multiscale_entropy(samples, m, r, scales)`, C# `Measurements.MultiscaleEntropy`): per scale
  `τ`, the sample entropy of `y[j] = (Σ_{i=jτ}^{jτ+τ−1} x[i]) / τ`, `j < floor(N/τ)`, with the
  same `r` at every scale. Scales not empty, each `≥ 1`, `floor(N/τ) ≥ m + 2`; otherwise as sample
  entropy. **(implemented)**
- **Fuzzy entropy** ([ADR 0339](adr/0339-fuzzy-entropy.md); `fuzzy_entropy(samples, m, r,
  n=2)`, C# `Measurements.FuzzyEntropy`): Chen's `ln φ_m − ln φ_{m+1}`; `M = N − m` templates of
  `k` samples minus their own mean, `d` the Chebyshev distance, `D = exp(−dⁿ/r)`,
  `φ_k = Σ_{i≠j} D / (M(M − 1))`. Real, finite, at least `m + 2` samples; integer `m ≥ 1`;
  finite `r > 0`, `n ≥ 1`. **(implemented)**
- **Rescaled range** ([ADR 0340](adr/0340-rescaled-range.md); `rescaled_range(samples, scales)`,
  C# `Measurements.RescaledRange`): per scale `s`, `B = floor(N/s)` boxes from the start; in each
  `Z_t = Σ_{u≤t} (x_u − mean)`, `R = max Z − min Z`, `S` the population standard deviation; the
  value is the mean `R/S`; `hurst` the least-squares slope of `ln` value against `ln s`. No
  small-sample correction. Result `(scales, values, hurst)`. At least two strictly increasing
  integer scales, `4 ≤ s ≤ N`; every box `S > 0`. **(implemented)**
- **Dispersion entropy** ([ADR 0341](adr/0341-dispersion-entropy.md);
  `dispersion_entropy(samples, m, classes, delay=1)`, C# `Measurements.DispersionEntropy`):
  `y = Φ((x − μ)/σ)`, `σ` the population standard deviation; class `min(c, floor(c·y) + 1)`;
  Shannon entropy of the `N − (m − 1)·delay` class patterns over `ln cᵐ`. Real, finite, not
  constant; `1 ≤ m ≤ 10`, `2 ≤ c ≤ 64`, `delay ≥ 1`; at least one pattern. **(implemented)**
- **SVD entropy** ([ADR 0342](adr/0342-svd-entropy.md); `svd_entropy(samples, order, delay=1)`,
  C# `Measurements.SvdEntropy`): the singular values `σ` of the `K × order` delay-embedding
  matrix (rows `x_i, x_{i+delay}, …`, mean not removed), `p = σ/Σσ`, `−Σ p ln p / ln(order)`.
  Real, finite, not all 0; `2 ≤ order ≤ 32`, `delay ≥ 1`, `K = N − (order − 1)·delay ≥ order`.
  **(implemented)**
- **Weighted permutation entropy** ([ADR 0343](adr/0343-weighted-permutation-entropy.md);
  `weighted_permutation_entropy(samples, order, delay=1)`, C#
  `Measurements.WeightedPermutationEntropy`): the windows and patterns of permutation entropy,
  each window weighted by its population variance; `p(π) = Σ w (pattern π) / Σ w`;
  `−Σ p ln p / ln(order!)`. Its rules, plus at least one window that varies. **(implemented)**
- **Increment entropy** ([ADR 0344](adr/0344-increment-entropy.md);
  `increment_entropy(samples, m, levels)`, C# `Measurements.IncrementEntropy`): increments
  `v = diff(x)`, `σ` their population deviation; letter `(sign v, min(R, floor(|v|·R/σ)))`; the
  Shannon entropy in nats of the `N − m` words of `m` letters, not normalized. Real, finite, at
  least `m + 1` samples, increments not all 0; `m ≥ 1`, `1 ≤ levels ≤ 1000`. **(implemented)**
- **Bubble entropy** ([ADR 0345](adr/0345-bubble-entropy.md); `bubble_entropy(samples, m)`,
  C# `Measurements.BubbleEntropy`): for `k = m` and `m + 1`, the swap count (strict inversions)
  of each of the `N − k + 1` windows; `H_k = −ln Σ p_s²`; `(H_{m+1} − H_m)/ln((m + 1)/(m − 1))`.
  Real, finite, at least `m + 1` samples; integer `2 ≤ m ≤ 64`. **(implemented)**
- **Attention entropy** ([ADR 0346](adr/0346-attention-entropy.md);
  `attention_entropy(samples)`, C# `Measurements.AttentionEntropy`): strict interior local
  maxima and minima; four interval sets (max to max, min to min, each max to the next min, each
  min to the next max); the mean of their Shannon entropies in nats. Real, finite; every set
  non-empty. **(implemented)**
- **Slope entropy** ([ADR 0347](adr/0347-slope-entropy.md); `slope_entropy(samples, m,
  gamma=1.0, delta=1e-3)`, C# `Measurements.SlopeEntropy`): each step `d` of a window of `m`
  samples becomes `+2` (`d > γ`), `+1` (`δ < d ≤ γ`), `0` (`|d| ≤ δ`), `−1` (`−γ ≤ d < −δ`) or
  `−2` (`d < −γ`); the Shannon entropy in nats of the `N − m + 1` patterns, not normalized.
  Real, finite, at least `m` samples; `2 ≤ m ≤ 16`; `0 ≤ δ < γ`, finite. **(implemented)**
- **Distribution entropy** ([ADR 0348](adr/0348-distribution-entropy.md);
  `distribution_entropy(samples, m, bins=512)`, C# `Measurements.DistributionEntropy`): the
  Chebyshev distances of all pairs `i < j` of the `N − m + 1` windows; bin
  `min(M − 1, floor((d − lo)·M/(hi − lo)))` over their range; `−Σ p ln p / ln M`; 0 if all
  distances are equal. Real, finite, at least `m + 1` samples; `m ≥ 1`;
  `2 ≤ bins ≤ 1 000 000`. **(implemented)**
- **Correlation sum** ([ADR 0349](adr/0349-correlation-sum.md); `correlation_sum(samples, m,
  radii, delay=1, theiler=0)`, C# `Measurements.CorrelationSum`): over the pairs `i < j` with
  `j − i > w` of the vectors `(x_i, x_{i+τ}, …, x_{i+(m−1)τ})`, `C(r)` is the share whose
  Chebyshev distance is strictly below `r`; `dimension` is the least-squares slope of
  `ln C` against `ln r`. Real, finite samples; `m, τ ≥ 1`, `w ≥ 0`, at least one pair; at
  least two radii, finite, positive, strictly increasing, each `C(r) > 0`. **(implemented)**
- **Recurrence quantification** ([ADR 0350](adr/0350-recurrence-quantification.md);
  `recurrence_quantification(samples, m, radius, delay=1, min_line=2, theiler=0)`, C#
  `Measurements.RecurrenceQuantification`): over the points `j − i > w` of the plot of
  vectors embedded as for the correlation sum, recurrent where the Chebyshev distance is
  strictly below `radius`; `rate` = recurrent / points; `determinism` = recurrent points on
  diagonal runs of at least `min_line` / recurrent points; `longest` = the longest run, 0 if
  none. Real, finite samples; `m, τ, min_line ≥ 1`, `w ≥ 0`; `radius` finite, positive; at
  least one point and one recurrent point. **(implemented)**
- **Fisher information** ([ADR 0351](adr/0351-fisher-information.md);
  `fisher_information(samples, order, delay=1)`, C# `Measurements.FisherInformation`): the
  singular values of SVD entropy's embedding, sorted largest first and divided by their sum,
  `σ̄_1 ≥ … ≥ σ̄_m`; `Σ_{i<m} (σ̄_{i+1} − σ̄_i)² / σ̄_i`, a term with `σ̄_i = 0` being 0. The
  rules are SVD entropy's. **(implemented)**
- **Auto mutual information** ([ADR 0352](adr/0352-auto-mutual-information.md);
  `auto_mutual_information(samples, lags, bins=16)`, C# `Measurements.AutoMutualInformation`):
  sample `x` in bin `min(B − 1, floor((x − lo)·B/(hi − lo)))` over the record's range; at lag
  `τ` the `n = N − τ` pairs `(x_t, x_{t+τ})` give `Σ (c_ab/n)·ln(c_ab·n/(c_a·c_b))` in nats,
  the marginals counted over the same pairs. Real, finite, not all equal; lags from 0 to
  `N − 1`, at least one; `2 ≤ bins ≤ 4096`. **(implemented)**
- **Rényi entropy** ([ADR 0353](adr/0353-renyi-entropy.md); `renyi_entropy(samples, alpha,
  bins=16)`, C# `Measurements.RenyiEntropy`): the samples binned as for auto mutual
  information; over the occupied bins, `ln K` at `α = 0`, `−Σ p ln p` at `α = 1`,
  `ln(Σ p^α)/(1 − α)` otherwise, in nats. Real, finite, not all equal; `α` finite, `≥ 0`;
  `2 ≤ bins ≤ 4096`. **(implemented)**
- **Largest Lyapunov exponent** ([ADR 0354](adr/0354-largest-lyapunov.md);
  `largest_lyapunov(samples, m, steps, delay=1, theiler=0)`, C# `Measurements.LargestLyapunov`):
  of the vectors embedded as for the correlation sum, the first `P = W − K` take part; each
  is paired with its Chebyshev-nearest `j'` with `|j − j'| > w`, the lowest on a tie;
  `divergence[k]`, `k = 0 … K`, is the mean of `ln d_j(k)` over the pairs with
  `d_j(k) > 0`; `exponent` is its least-squares slope against `k`. Real, finite samples;
  `m, τ, K ≥ 1`, `w ≥ 0`; `P ≥ 2w + 2`; some `d_j(k) > 0` at every `k`. **(implemented)**
- **Aggregated variance** ([ADR 0355](adr/0355-aggregated-variance.md);
  `aggregated_variance(samples, sizes)`, C# `Measurements.AggregatedVariance`): at size `s`,
  the population variance (over `B = floor(N/s)`) of the means of the first `B` blocks of
  `s` samples; `hurst = 1 + β/2`, `β` the least-squares slope of `ln values` against `ln s`.
  Real, finite samples; at least two sizes, strictly increasing, from 1 to `N/2`; every
  value above 0. **(implemented)**
- **Tsallis entropy** ([ADR 0356](adr/0356-tsallis-entropy.md); `tsallis_entropy(samples, q,
  bins=16)`, C# `Measurements.TsallisEntropy`): the samples binned as for auto mutual
  information; over the occupied bins, `−Σ p ln p` at `q = 1`, `(1 − Σ p^q)/(q − 1)`
  otherwise. Real, finite, not all equal; `q` finite, `≥ 0`; `2 ≤ bins ≤ 4096`.
  **(implemented)**
- **Time irreversibility** ([ADR 0357](adr/0357-time-irreversibility.md);
  `time_irreversibility(samples, lag=1)`, C# `Measurements.TimeIrreversibility`): with
  `Δ_t = x_{t+τ} − x_t`, `t = 0 … N − τ − 1`, and `M_k` the mean of `Δ^k`, the value is
  `M_3/(M_2·√M_2)`; reversing the record negates it. Real, finite samples;
  `1 ≤ lag ≤ N − 1`; `M_2 > 0`. **(implemented)**
- **Cosine similarity entropy** ([ADR 0358](adr/0358-cosine-similarity-entropy.md);
  `cosine_similarity_entropy(samples, m, r, delay=1)`, C# `Measurements.CosineSimilarityEntropy`):
  vectors `v_i = (x_i, …, x_{i+(m−1)τ})`, `i < W = N − (m − 1)τ`; angular distance
  `arccos(c)/π` of the clipped cosine similarity; `B` the share of pairs `i < j` with distance
  strictly below `r`; value `−B log2 B − (1 − B) log2(1 − B)` bits, `0 log 0 = 0`. No mean
  removal. Real, finite; `m, delay ≥ 1`; `W ≥ 2`; `0 < r ≤ 1`; no all-zero vector.
  **(implemented)**
- **Ljung–Box statistic** ([ADR 0359](adr/0359-ljung-box.md); `ljung_box(samples, lags)`,
  C# `Measurements.LjungBox`): with the biased, mean-removed
  `ρ_k = Σ_{t<N−k} (x_t − x̄)(x_{t+k} − x̄) / Σ (x_t − x̄)²`, the value is
  `Q = N(N + 2) Σ_{k=1}^{h} ρ_k²/(N − k)`; no p-value. Real, finite, not all equal;
  `1 ≤ lags ≤ N − 1`. **(implemented)**
- **Turning point test** ([ADR 0360](adr/0360-turning-points.md); `turning_points(samples)` →
  `TurningPoints(count, z)`, C# `Measurements.TurningPoints`): `count` is the number of
  `1 ≤ i ≤ N − 2` with `x_i` strictly above or strictly below both neighbours (a tie is not a
  turning point); `z = (count − 2(N − 2)/3)/√((16N − 29)/90)`. Real, finite; `N ≥ 3`.
  **(implemented)**
- **Runs test** ([ADR 0361](adr/0361-runs-test.md); `runs_test(samples)` → `RunsTest(runs, z)`,
  C# `Measurements.RunsTest`): samples above the float mean (sum / N) labelled +, below −,
  equal dropped; `runs` the number of blocks of equal labels; `n₁`, `n₂` the label counts,
  `n = n₁ + n₂`; `z = (runs − 2n₁n₂/n − 1)/√(2n₁n₂(2n₁n₂ − n)/(n²(n − 1)))`. Real, finite;
  the variance must be above 0. **(implemented)**
- **von Neumann ratio** ([ADR 0362](adr/0362-von-neumann-ratio.md); `von_neumann_ratio(samples)`,
  C# `Measurements.VonNeumannRatio`): the plain ratio
  `Σ_{t<N−1} (x_{t+1} − x_t)² / Σ_t (x_t − x̄)²`, not von Neumann's `δ²/s²`, which is
  `N/(N − 1)` times it; about 2 for an i.i.d. record. Real, finite; `N ≥ 2`; not all equal.
  **(implemented)**
- **Bartels rank test** ([ADR 0363](adr/0363-bartels-rank-test.md); `bartels_rank_test(samples)` →
  `BartelsRankTest(ratio, z)`, C# `Measurements.BartelsRankTest`): ranks 1 … N, ties given the
  mean rank; `ratio = Σ (R_{t+1} − R_t)² / Σ (R_t − R̄)²` (the actual denominator);
  `z = (ratio − 2)/√(4(N − 2)(5N² − 2N − 9)/(5N(N + 1)(N − 1)²))`, not adjusted for ties.
  Real, finite; `N ≥ 3`; not all equal. **(implemented)**
- **Mann–Kendall trend test** ([ADR 0364](adr/0364-mann-kendall.md); `mann_kendall(samples)` →
  `MannKendall(s, z)`, C# `Measurements.MannKendall`): `S = Σ_{i<j} sign(x_j − x_i)`;
  `σ² = (N(N − 1)(2N + 5) − Σ t(t − 1)(2t + 5))/18` over the groups of equal samples;
  `z = (S ∓ 1)/σ` for `S ≷ 0`, 0 at `S = 0`. Real, finite; `N ≥ 2`; not all equal.
  **(implemented)**
- **Sen's slope** ([ADR 0365](adr/0365-sens-slope.md); `sens_slope(samples)`, C#
  `Measurements.SensSlope`): the median of `(x_j − x_i)/(j − i)` over every `i < j`, per
  sample; `(a + b)/2` of the two middle slopes for an even count. Real, finite; `N ≥ 2`.
  **(implemented)**
- **Pettitt change-point test** ([ADR 0366](adr/0366-pettitt.md); `pettitt(samples)` →
  `Pettitt(statistic, index, p_value)`, C# `Measurements.Pettitt`): `U_t = Σ_{i≤t<j}
  sign(x_j − x_i)` for `t = 0 … N − 2`; `K = max |U_t|`; `index` the smallest `t` reaching it
  (the last sample before the change); `p_value = min(1, 2 exp(−6K²/(N³ + N²)))`. Real,
  finite; `N ≥ 2`. **(implemented)**
- **Buishand range test** ([ADR 0367](adr/0367-buishand-range.md); `buishand_range(samples)` →
  `BuishandRange(q, r, index)`, C# `Measurements.BuishandRange`): float mean `(Σ x)/N`;
  `S_k = Σ_{i≤k} (x_i − x̄)`, `k = 0 … N − 1`, in order; population `σ`;
  `q = max |S_k|/σ`; `r = (max(0, max S) − min(0, min S))/σ`; `index` the smallest `k` with
  the largest `|S_k|`. Real, finite; `N ≥ 2`; not all equal. **(implemented)**
- **Standard normal homogeneity test** ([ADR 0368](adr/0368-snht.md); `snht(samples)` →
  `Snht(statistic, index)`, C# `Measurements.Snht`): float mean `(Σ x)/N`, population `σ²`;
  `T_k = N S_k²/(k(N − k)σ²)` for `k = 1 … N − 1` (equal to `k z̄₁² + (N − k) z̄₂²`), with
  `S_k` the in-order sum of the first `k` deviations; `statistic = max T_k`; `index = k − 1`
  for the smallest `k` reaching it. Real, finite; `N ≥ 2`; not all equal. **(implemented)**
- **Spearman rank correlation** ([ADR 0369](adr/0369-spearman.md);
  `spearman_correlation(x, y)`, C# `Measurements.SpearmanCorrelation`): each record ranked from
  1, ties given the mean rank; `c = (N + 1)/2`;
  `rho = Σ (r − c)(s − c)/√(Σ (r − c)² · Σ (s − c)²)`, the product, then the square root, then
  the quotient. Real, finite, equal lengths; `N ≥ 2`; neither record constant.
  **(implemented)**
- **Kendall's tau-b** ([ADR 0370](adr/0370-kendall-tau.md); `kendall_tau(x, y)`, C#
  `Measurements.KendallTau`): `n_c − n_d = Σ_{i<j} sign(x_j − x_i) sign(y_j − y_i)`;
  `n₀ = N(N − 1)/2`; `n₁`, `n₂` = `Σ t(t − 1)/2` over the tie groups of `x` and of `y`;
  `tau = (n_c − n_d)/√((n₀ − n₁)(n₀ − n₂))`, the product in float before the square root.
  Real, finite, equal lengths; `N ≥ 2`; neither record constant. **(implemented)**
- **Correlations, scaled first** ([ADR 0627](adr/0627-correlations-scaled-first.md)): the
  Pearson correlation, distance correlation and biweight midcorrelation divide each checked
  record by its largest magnitude, when that is positive, before forming any deviation, so
  no square overflows or underflows. **(implemented)**
- **Pearson correlation** ([ADR 0371](adr/0371-pearson.md); `pearson_correlation(x, y)`, C#
  `Measurements.PearsonCorrelation`): float means `(Σ x)/N`, `(Σ y)/N`;
  `r = Σ (x − x̄)(y − ȳ)/√(Σ (x − x̄)² · Σ (y − ȳ)²)`, the product, then the square root, then
  the quotient; not clamped. Real, finite, equal lengths; `N ≥ 2`; neither record constant.
  **(implemented)**
- **Distance correlation** ([ADR 0372](adr/0372-distance-correlation.md);
  `distance_correlation(x, y)`, C# `Measurements.DistanceCorrelation`): `a_ij = |x_i − x_j|`,
  double-centred `A_ij = a_ij − ā_i· − ā_·j + ā_··` (likewise `B`); V-statistics
  `dCov² = ΣAB/N²`, `dVar² = ΣA²/N²`; `dCor = √(max(0, dCov²)/√(dVar²(x) dVar²(y)))`. Real,
  finite, equal lengths; `N ≥ 2`; neither record constant. **(implemented)**
- **Biweight midcorrelation** ([ADR 0373](adr/0373-biweight-midcorrelation.md);
  `biweight_midcorrelation(x, y)`, C# `Measurements.BiweightMidcorrelation`): median `m`
  (`(a + b)/2` for an even count), unscaled `MAD` = median of `|x − m|`;
  `u = (x − m)/(9·MAD)`; `w = (1 − u·u)(1 − u·u)` for `|u| < 1`, else 0; `a = (x − m)w`, `b`
  likewise; `Σab/√(Σa² · Σb²)`. Real, finite, equal lengths; `N ≥ 2`; neither `MAD` 0.
  **(implemented)**
- **Hoeffding's D** ([ADR 0374](adr/0374-hoeffding-d.md); `hoeffding_d(x, y)`, C#
  `Measurements.HoeffdingD`): mean ranks `R`, `S`; `Q_i = 1 + Σ_{j≠i} φ(x_j, x_i)φ(y_j, y_i)`,
  `φ` = 1 below, 1/2 equal, 0 above; `D₁ = Σ(Q−1)(Q−2)`, `D₂ = Σ(R−1)(R−2)(S−1)(S−2)`,
  `D₃ = Σ(R−2)(S−2)(Q−1)`; `D = 30((N−2)(N−3)D₁ + D₂ − 2(N−2)D₃)/(N(N−1)(N−2)(N−3)(N−4))`,
  1 for a monotone pair without ties. Real, finite, equal lengths; `N ≥ 5`. **(implemented)**
- **Blomqvist's beta** ([ADR 0375](adr/0375-blomqvist-beta.md); `blomqvist_beta(x, y)`, C#
  `Measurements.BlomqvistBeta`): medians the middle value, or `(a + b)/2` of the two middle
  values for even `N`; samples on either median dropped; `β = (n₊ − n₋)/(n₊ + n₋)` with `n₊`
  the samples on the same side of both medians and `n₋` on opposite sides. Real, finite, equal
  lengths; at least one sample off both medians. **(implemented)**
- **Chatterjee's xi** ([ADR 0376](adr/0376-chatterjee-xi.md); `chatterjee_xi(x, y)`, C#
  `Measurements.ChatterjeeXi`): pairs sorted by `x`, ties in `x` kept in record order (not at
  random); `r_i = #{j: y_j ≤ y_(i)}`, `l_i = #{j: y_j ≥ y_(i)}`;
  `ξ = 1 − N Σ|r_{i+1} − r_i| / (2 Σ l_i(N − l_i))`, sums exact integers. Not symmetric. Real,
  finite, equal lengths; `N ≥ 2`, `y` not constant. **(implemented)**
- **Goodman and Kruskal's gamma** ([ADR 0377](adr/0377-goodman-kruskal-gamma.md);
  `goodman_kruskal_gamma(x, y)`, C# `Measurements.GoodmanKruskalGamma`): over pairs `i < j`,
  `C` concordant and `D` discordant by comparison, pairs tied in either record in neither;
  `γ = (C − D)/(C + D)`. Real, finite, equal lengths; `C + D > 0`. **(implemented)**
- **Somers' D** ([ADR 0378](adr/0378-somers-d.md); `somers_d(x, y)`, C#
  `Measurements.SomersD`): `d_yx`, `y` predicted from `x`; `C`, `D` as for Goodman and
  Kruskal's gamma, `T_x` the pairs tied in `x`; `d_yx = (C − D)/(N(N − 1)/2 − T_x)`. Real,
  finite, equal lengths; at least one pair untied in `x`. **(implemented)**
- **Kendall's W** ([ADR 0379](adr/0379-kendall-w.md); `kendall_w(ratings)`, C#
  `Measurements.KendallW`): rows are raters, columns items; each row ranked from 1 with mean
  ranks; `R_j` the column sums of the ranks, `S = Σ(R_j − m(n + 1)/2)²`, `T = Σ(t³ − t)` per
  rater; `W = 12S/(m²(n³ − n) − mΣT)`. Real, finite, 2-D; `m ≥ 2`, `n ≥ 2`; not every row
  constant. **(implemented)**
- **Cronbach's alpha** ([ADR 0380](adr/0380-cronbach-alpha.md); `cronbach_alpha(scores)`, C#
  `Measurements.CronbachAlpha`): rows are items, columns subjects; `σ_i²` the sample variance
  (`N − 1`) of row `i`, `σ_t²` that of the column sums; `α = k/(k − 1)(1 − Σσ_i²/σ_t²)`.
  Real, finite, 2-D; `k ≥ 2`, `N ≥ 2`; `σ_t² > 0`. **(implemented)**
- **ICC(3,1)** ([ADR 0381](adr/0381-icc-consistency.md); `icc_consistency(ratings)`, C#
  `Measurements.IccConsistency`): rows are raters, columns subjects; `SS_S = kΣ(c_j − x̄)²`,
  `SS_E = Σ(x_ij − r_i − c_j + x̄)²`, `MS_S = SS_S/(n − 1)`, `MS_E = SS_E/((n − 1)(k − 1))`;
  `(MS_S − MS_E)/(MS_S + (k − 1)MS_E)`. Real, finite, 2-D; `k ≥ 2`, `n ≥ 2`; denominator
  positive. **(implemented)**
- **Fleiss' kappa** ([ADR 0382](adr/0382-fleiss-kappa.md); `fleiss_kappa(counts)`, C#
  `Measurements.FleissKappa`): rows are subjects, columns categories, entries the raters
  choosing that category; `p_j = Σ_i n_ij/(Nn)`, `P̄_e = Σp_j²`,
  `P_i = (Σ_j n_ij² − n)/(n(n − 1))`; `κ = (P̄ − P̄_e)/(1 − P̄_e)`. Whole, not negative,
  2-D; `N ≥ 1`, `q ≥ 2`; equal row sums `n ≥ 2`; `P̄_e < 1`. **(implemented)**
- **Cohen's kappa** ([ADR 0383](adr/0383-cohen-kappa.md); `cohen_kappa(a, b)`, C#
  `Measurements.CohenKappa`): categories are the distinct values, compared with `==`; `A`
  the items with `a_i = b_i`, `E = Σ_c a_c b_c` from the counts per category;
  `κ = (NA − E)/(N² − E)`. Real, finite, equal lengths, `N ≥ 1`; `E < N²`. **(implemented)**
- **Scott's pi** ([ADR 0384](adr/0384-scott-pi.md); `scott_pi(a, b)`, C#
  `Measurements.ScottPi`): categories as for Cohen's kappa; `A` the items with `a_i = b_i`,
  `F = Σ_c (a_c + b_c)²`; `π = (4NA − F)/(4N² − F)`. Real, finite, equal lengths, `N ≥ 1`;
  `F < 4N²`. **(implemented)**
- **Matthews correlation** ([ADR 0385](adr/0385-matthews-correlation.md);
  `matthews_correlation(truth, decision)`, C# `Measurements.MatthewsCorrelation`): values 0
  and 1, 1 positive; `(TP·TN − FP·FN)/√((TP + FP)(TP + FN)(TN + FP)(TN + FN))`, the product
  in `double` in that order. Equal lengths, `N ≥ 1`; both classes in both records.
  **(implemented)**
- **F1 score** ([ADR 0386](adr/0386-f1-score.md); `f1_score(truth, decision)`, C#
  `Measurements.F1Score`): records as for the Matthews correlation; `2TP/(2TP + FP + FN)`.
  Equal lengths, `N ≥ 1`; at least one positive in either record. **(implemented)**
- **Youden's J** ([ADR 0387](adr/0387-youden-j.md); `youden_j(truth, decision)`, C#
  `Measurements.YoudenJ`): records as for the Matthews correlation;
  `(TP·TN − FP·FN)/((TP + FN)(TN + FP))`, sensitivity plus specificity less 1. Equal
  lengths, `N ≥ 1`; both classes in the truth. **(implemented)**
- **Jaccard index** ([ADR 0388](adr/0388-jaccard-index.md); `jaccard_index(truth,
  decision)`, C# `Measurements.JaccardIndex`): records as for the Matthews correlation;
  `TP/(TP + FP + FN)`. Equal lengths, `N ≥ 1`; at least one 1 in either record.
  **(implemented)**
- **Fowlkes–Mallows index** ([ADR 0389](adr/0389-fowlkes-mallows-index.md);
  `fowlkes_mallows_index(truth, decision)`, C# `Measurements.FowlkesMallowsIndex`): records
  as for the Matthews correlation; `TP/√((TP + FP)(TP + FN))`, the product in `double`.
  Equal lengths, `N ≥ 1`; a 1 in each record. **(implemented)**
- **Diagnostic odds ratio** ([ADR 0390](adr/0390-diagnostic-odds-ratio.md);
  `diagnostic_odds_ratio(truth, decision)`, C# `Measurements.DiagnosticOddsRatio`): records
  as for the Matthews correlation; `(TP·TN)/(FP·FN)`, no continuity correction. Equal
  lengths, `N ≥ 1`; `FP > 0` and `FN > 0`. **(implemented)**
- **Brier score** ([ADR 0391](adr/0391-brier-score.md); `brier_score(outcome, probability)`,
  C# `Measurements.BrierScore`): outcomes 0 or 1, probabilities in `[0, 1]`;
  `(1/N)·Σ (pᵢ − yᵢ)²`, summed in order. Equal lengths, `N ≥ 1`. **(implemented)**
- **Log loss** ([ADR 0392](adr/0392-log-loss.md); `log_loss(outcome, probability)`, C#
  `Measurements.LogLoss`): records as for the Brier score; `−(1/N)·Σ ℓᵢ` in nats, `ℓᵢ = ln pᵢ`
  for `yᵢ = 1` and `ln(1 − pᵢ)` for `yᵢ = 0`, only that term formed; no clipping. A certain
  wrong forecast is an error. **(implemented)**
- **ROC AUC** ([ADR 0393](adr/0393-roc-auc.md); `roc_auc(truth, score)`, C#
  `Measurements.RocAuc`): truth 0 or 1, scores finite, higher meaning positive;
  `(R₁ − n₁(n₁ + 1)/2)/(n₁·n₀)` from mean ranks, a tied pair counting 1/2. Equal lengths; at
  least one positive and one negative. **(implemented)**
- **Average precision** ([ADR 0394](adr/0394-average-precision.md);
  `average_precision(truth, score)`, C# `Measurements.AveragePrecision`): records as for the
  ROC AUC; thresholds the distinct scores from the highest down, `(1/n₁)·Σ kτ·Tτ/Dτ`, no
  interpolation, ties one threshold. Equal lengths; at least one positive. **(implemented)**
- **Markedness** ([ADR 0395](adr/0395-markedness.md); `markedness(truth, decision)`, C#
  `Measurements.Markedness`): records as for the Matthews correlation;
  `(TP·TN − FP·FN)/((TP + FP)(TN + FN))`, one division of whole numbers in `double`. Equal
  lengths, `N ≥ 1`; the decision holds a 1 and a 0. **(implemented)**
- **Balanced accuracy** ([ADR 0396](adr/0396-balanced-accuracy.md);
  `balanced_accuracy(truth, decision)`, C# `Measurements.BalancedAccuracy`): records as for
  the Matthews correlation; `(TP·(TN + FP) + TN·(TP + FN))/(2·(TP + FN)·(TN + FP))`, one
  division of whole numbers in `double`. Equal lengths, `N ≥ 1`; the truth holds a 1 and a 0.
  **(implemented)**
- **Effect sizes, scaled together** ([ADR 0628](adr/0628-effect-sizes-scaled-together.md)):
  Cohen's d, Hedges' g and Glass's delta scale both checked records by the power of 2 that
  brings the largest magnitude in either into [1, 2), when that is positive, before forming
  any mean or deviation, so no square overflows or underflows. The scaling is exact. **(implemented)**
- **Cohen's d** ([ADR 0397](adr/0397-cohen-d.md); `cohen_d(x, y)`, C# `Measurements.CohenD`):
  `(x̄ − ȳ)/s`, `s` the pooled standard deviation over `n_x + n_y − 2`; positive when `x` has
  the larger mean. Each sample at least 2, finite; `s > 0`. **(implemented)**
- **Hedges' g** ([ADR 0398](adr/0398-hedges-g.md); `hedges_g(x, y)`, C#
  `Measurements.HedgesG`): Cohen's d times the exact `J(m) = Γ(m/2)/(√(m/2)·Γ((m − 1)/2))`,
  `m = n_x + n_y − 2`, from a log-gamma difference; rules as for Cohen's d. **(implemented)**
- **Glass's delta** ([ADR 0399](adr/0399-glass-delta.md); `glass_delta(x, y)`, C#
  `Measurements.GlassDelta`): `(x̄ − ȳ)/s_y`, `x` treated and `y` the control, `s_y` its sample
  standard deviation over `n_y − 1`. `n_x ≥ 1`, `n_y ≥ 2`, finite; `s_y > 0`. **(implemented)**
- **Cliff's delta** ([ADR 0400](adr/0400-cliff-delta.md); `cliff_delta(x, y)`, C#
  `Measurements.CliffDelta`): `(#(xᵢ > yⱼ) − #(xᵢ < yⱼ))/(n_x·n_y)` over every pair, ties in
  neither count; one division of whole numbers in `double`. Each sample at least 1, finite.
  **(implemented)**
- **Vargha–Delaney A** ([ADR 0401](adr/0401-vargha-delaney-a.md); `vargha_delaney_a(x, y)`,
  C# `Measurements.VarghaDelaneyA`): `(2·#(xᵢ > yⱼ) + #(xᵢ = yⱼ))/(2·n_x·n_y)`, one division of
  whole numbers in `double`, not formed from Cliff's delta. Rules as for Cliff's delta.
  **(implemented)**
- **Two-sample Kolmogorov–Smirnov statistic** ([ADR 0402](adr/0402-kolmogorov-smirnov.md);
  `kolmogorov_smirnov(x, y)`, C# `Measurements.KolmogorovSmirnov`): `max_t |F_x(t) − F_y(t)|`
  over the pooled values, as the whole number `|#(x ≤ t)·n_y − #(y ≤ t)·n_x|` divided once by
  `n_x·n_y`. Each sample at least 1, finite. **(implemented)**
- **First Wasserstein distance** ([ADR 0403](adr/0403-wasserstein-distance.md);
  `wasserstein_distance(x, y)`, C# `Measurements.WassersteinDistance`): `∫|F_x − F_y| dt` as
  `Σ g_m·(t_{m+1} − t_m)` over the distinct pooled values in order, `g_m` the whole number
  `|#(x ≤ t_m)·n_y − #(y ≤ t_m)·n_x|`, then one division by `n_x·n_y`. Each sample at least 1,
  finite. **(implemented)**
- **Energy distance** ([ADR 0404](adr/0404-energy-distance.md); `energy_distance(x, y)`, C#
  `Measurements.EnergyDistance`): `2A − B − C`, the mean of `|xᵢ − yⱼ|` over all pairs and of
  `|xᵢ − xₖ|`, `|yⱼ − yₗ|` over all ordered pairs with equal indices; the squared form, no root.
  Each sum a double loop in order; below 0 from rounding gives 0. Each sample at least 1,
  finite. **(implemented)**
- **Two-sample Cramér–von Mises statistic** ([ADR 0405](adr/0405-cramer-von-mises.md);
  `cramer_von_mises(x, y)`, C# `Measurements.CramerVonMises`): `n_x·n_y/N² · Σ_k (F_x(z_k) −
  F_y(z_k))²` over every pooled value with its multiplicity (Anderson 1962). Summed as `c·g²`
  per distinct value in increasing order, `g = |#(x ≤ t)·n_y − #(y ≤ t)·n_x|`, then one
  division by `n_x·n_y·N²`. Each sample at least 1, finite. **(implemented)**
- **Hodges–Lehmann shift estimate** ([ADR 0406](adr/0406-hodges-lehmann.md);
  `hodges_lehmann(x, y)`, C# `Measurements.HodgesLehmann`): the median of the `n_x·n_y`
  differences `xᵢ − yⱼ` in `double`; with an even count `(a + b)/2` of the middle two. Each
  sample at least 1, finite. **(implemented)**
- **Kullback–Leibler divergence** ([ADR 0407](adr/0407-kl-divergence.md);
  `kl_divergence(p, q)`, C# `Measurements.KlDivergence`): `Σ Pᵢ·ln(Pᵢ/Qᵢ)` in nats, `P` and `Q`
  each divided by its largest value, then by the in-order sum of those quotients, so no sum
  overflows (ADR 0624); terms with `pᵢ = 0` dropped; below 0 from
  rounding gives 0. Equal lengths at least 1, finite, non-negative, each sum above 0; `qᵢ = 0`
  where `pᵢ > 0` is an error. **(implemented)**
- **Jensen–Shannon divergence** ([ADR 0408](adr/0408-js-divergence.md);
  `js_divergence(p, q)`, C# `Measurements.JsDivergence`): `½·Σ [Pᵢ·ln(Pᵢ/Mᵢ) + Qᵢ·ln(Qᵢ/Mᵢ)]`
  in nats, `Mᵢ = (Pᵢ + Qᵢ)/2`, zero terms dropped, the `P` term first; clamped to `[0, ln 2]`.
  Inputs as for the Kullback–Leibler divergence, zeros allowed anywhere. **(implemented)**
- **Hellinger distance** ([ADR 0409](adr/0409-hellinger-distance.md);
  `hellinger_distance(p, q)`, C# `Measurements.HellingerDistance`): `√(½·Σ(√Pᵢ − √Qᵢ)²)`, the
  squared root differences summed in order, clamped to at most 1; not `√(1 − Σ√(PᵢQᵢ))`.
  Inputs as for the Jensen–Shannon divergence. **(implemented)**
- **Bhattacharyya distance** ([ADR 0410](adr/0410-bhattacharyya-distance.md);
  `bhattacharyya_distance(p, q)`, C# `Measurements.BhattacharyyaDistance`): `0 − ln BC`,
  `BC = Σ√(Pᵢ·Qᵢ)` summed in order and clamped to at most 1. Inputs as for the Hellinger
  distance; `BC = 0` is an error. **(implemented)**
- **Total variation distance** ([ADR 0411](adr/0411-total-variation-distance.md);
  `total_variation_distance(p, q)`, C# `Measurements.TotalVariationDistance`): `½·Σ|Pᵢ − Qᵢ|`,
  summed in order, clamped to at most 1. Inputs as for the Hellinger distance.
  **(implemented)**
- **Pearson chi-square divergence** ([ADR 0412](adr/0412-chi-square-divergence.md);
  `chi_square_divergence(p, q)`, C# `Measurements.ChiSquareDivergence`): `Σ (Pᵢ − Qᵢ)²/Qᵢ`,
  summed in order; indices with `pᵢ = qᵢ = 0` dropped. Inputs as for the Kullback–Leibler
  divergence; `qᵢ = 0` where `pᵢ > 0` is an error. **(implemented)**
- **Rényi divergence** ([ADR 0413](adr/0413-renyi-divergence.md);
  `renyi_divergence(p, q, alpha)`, C# `Measurements.RenyiDivergence`):
  `ln(Σ pow(Pᵢ, α)·pow(Qᵢ, 1 − α))/(α − 1)`, summed in order over `pᵢ > 0` (and `qᵢ > 0` for
  `α < 1`), a result below zero clamped to `0`. `alpha` finite, above 0, not 1. Inputs as for
  the Kullback–Leibler divergence; an infinite divergence is an error. **(implemented)**
- **Jeffreys divergence** ([ADR 0414](adr/0414-jeffreys-divergence.md);
  `jeffreys_divergence(p, q)`, C# `Measurements.JeffreysDivergence`):
  `Σ (Pᵢ − Qᵢ)·ln(Pᵢ/Qᵢ)`, summed in order; indices zero in both dropped. Inputs as for the
  Kullback–Leibler divergence; an index zero in only one is an error. **(implemented)**
- **Cross-entropy** ([ADR 0415](adr/0415-cross-entropy.md); `cross_entropy(p, q)`,
  C# `Measurements.CrossEntropy`): `0 − Σ Pᵢ·ln Qᵢ` in nats, summed in order over `pᵢ > 0`.
  Inputs as for the Kullback–Leibler divergence; `qᵢ = 0` where `pᵢ > 0` is an error.
  **(implemented)**
- **Triangular discrimination** ([ADR 0416](adr/0416-triangular-discrimination.md);
  `triangular_discrimination(p, q)`, C# `Measurements.TriangularDiscrimination`):
  `Σ (Pᵢ − Qᵢ)²/(Pᵢ + Qᵢ)`, summed in order, indices zero in both dropped, clamped to at
  most 2. Inputs as for the Hellinger distance. **(implemented)**
- **Canberra distance** ([ADR 0417](adr/0417-canberra-distance.md);
  `canberra_distance(x, y)`, C# `Measurements.CanberraDistance`):
  `Σ |xᵢ − yᵢ|/(|xᵢ| + |yᵢ|)`, summed in order, indices zero in both dropped. `x` and `y`
  real, finite, of equal length at least 1; not normalized. **(implemented)**
- **Bray–Curtis dissimilarity** ([ADR 0418](adr/0418-bray-curtis.md); `bray_curtis(x, y)`,
  C# `Measurements.BrayCurtis`): `Σ|xᵢ − yᵢ| / Σ(xᵢ + yᵢ)`, both sums in order in one pass,
  clamped to at most 1. `x` and `y` finite, non-negative, of equal length at least 1, not
  both all zero; not normalized. **(implemented)**
- **Minkowski distance** ([ADR 0419](adr/0419-minkowski-distance.md);
  `minkowski_distance(x, y, order)`, C# `Measurements.MinkowskiDistance`):
  `m·pow(Σ pow(|xᵢ − yᵢ|/m, p), 1/p)`, `m` the largest difference (`0` when `m = 0`), the
  terms summed in order. `order` finite, at least 1; `x` and `y` real, finite, of equal
  length at least 1; a difference that overflows is an error. **(implemented)**
- **Chebyshev distance** ([ADR 0420](adr/0420-chebyshev-distance.md);
  `chebyshev_distance(x, y)`, C# `Measurements.ChebyshevDistance`): `max |xᵢ − yᵢ|`, exact.
  Inputs as for the Minkowski distance. **(implemented)**
- **Hamming distance** ([ADR 0421](adr/0421-hamming-distance.md); `hamming_distance(x, y)`,
  C# `Measurements.HammingDistance`): the count of indices with `xᵢ ≠ yᵢ` as doubles (`0.0`
  equals `−0.0`), an int. `x` and `y` real, finite, of equal length at least 1.
  **(implemented)**
- **Overlap coefficient** ([ADR 0422](adr/0422-overlap-coefficient.md);
  `overlap_coefficient(truth, decision)`, C# `Measurements.OverlapCoefficient`):
  `|A ∩ B| / min(|A|, |B|)` from integer counts. Records as for the Jaccard index; either
  with no 1 is an error. **(implemented)**
- **Tversky index** ([ADR 0423](adr/0423-tversky-index.md);
  `tversky_index(truth, decision, alpha, beta)`, C# `Measurements.TverskyIndex`):
  `TP / ((TP + α·FN) + β·FP)`, the denominator summed in that order. Records as for the
  Jaccard index; `alpha` and `beta` finite and at least 0; a zero denominator is an error.
  **(implemented)**
- **Simple matching coefficient** ([ADR 0424](adr/0424-simple-matching-coefficient.md);
  `simple_matching_coefficient(truth, decision)`, C# `Measurements.SimpleMatchingCoefficient`):
  `(TP + TN) / n` from integer counts. Records as for the Jaccard index. **(implemented)**
- **Rogers-Tanimoto coefficient** ([ADR 0425](adr/0425-rogers-tanimoto-coefficient.md);
  `rogers_tanimoto_coefficient(truth, decision)`, C# `Measurements.RogersTanimotoCoefficient`):
  `m / (m + 2u)`, `m` the agreements and `u` the disagreements, from integer counts. Records
  as for the Jaccard index. **(implemented)**
- **Russell-Rao coefficient** ([ADR 0426](adr/0426-russell-rao-coefficient.md);
  `russell_rao_coefficient(truth, decision)`, C# `Measurements.RussellRaoCoefficient`):
  `TP / n` from integer counts. Records as for the Jaccard index. **(implemented)**
- **Sokal-Sneath coefficient** ([ADR 0427](adr/0427-sokal-sneath-coefficient.md);
  `sokal_sneath_coefficient(truth, decision)`, C# `Measurements.SokalSneathCoefficient`):
  `TP / (TP + 2·(FN + FP))` from integer counts. Records as for the Jaccard index; neither
  holding a 1 is an error. **(implemented)**
- **Kulczynski coefficient** ([ADR 0428](adr/0428-kulczynski-coefficient.md);
  `kulczynski_coefficient(truth, decision)`, C# `Measurements.KulczynskiCoefficient`):
  `(TP/|A| + TP/|B|) / 2`, evaluated in that order from integer counts. Records as for the
  Jaccard index; either with no 1 is an error. **(implemented)**
- **Ochiai coefficient** ([ADR 0429](adr/0429-ochiai-coefficient.md);
  `ochiai_coefficient(truth, decision)`, C# `Measurements.OchiaiCoefficient`):
  `TP / √(|A|·|B|)`, the integer product rooted once. Records as for the Jaccard index;
  either with no 1 is an error. **(implemented)**
- **Yule's Q** ([ADR 0430](adr/0430-yule-q.md); `yule_q(truth, decision)`, C#
  `Measurements.YuleQ`): `(x − y) / (x + y)` with `x = TP·TN` and `y = FN·FP` as exact
  integers, each converted to a double once. Records as for the Jaccard index; `x + y = 0`
  is an error. **(implemented)**
- **Yule's Y** ([ADR 0431](adr/0431-yule-y.md); `yule_y(truth, decision)`, C#
  `Measurements.YuleY`): `(√x − √y) / (√x + √y)`, `x` and `y` as for Yule's Q, each
  converted to a double once and rooted once. Rules as for Yule's Q. **(implemented)**
- **Hamann coefficient** ([ADR 0432](adr/0432-hamann-coefficient.md);
  `hamann_coefficient(truth, decision)`, C# `Measurements.HamannCoefficient`):
  `(agreements − disagreements) / n`, an exact integer over the length. Records as for the
  Jaccard index. **(implemented)**
- **Baroni-Urbani-Buser coefficient** ([ADR 0433](adr/0433-baroni-urbani-buser-coefficient.md);
  `baroni_urbani_buser_coefficient(truth, decision)`, C#
  `Measurements.BaroniUrbaniBuserCoefficient`): `(r + TP) / (r + k)` with `r = √(TP·TN)`,
  the integer product converted to a double once and rooted once, and `k = TP + FN + FP`.
  Records as for the Jaccard index; both all 0 is an error. **(implemented)**
- **Sorgenfrei coefficient** ([ADR 0434](adr/0434-sorgenfrei-coefficient.md);
  `sorgenfrei_coefficient(truth, decision)`, C# `Measurements.SorgenfreiCoefficient`):
  `TP² / (|A|·|B|)`, both integers converted to doubles once, then one division. Records as
  for the Jaccard index; either with no 1 is an error. **(implemented)**
- **Forbes coefficient** ([ADR 0435](adr/0435-forbes-coefficient.md);
  `forbes_coefficient(truth, decision)`, C# `Measurements.ForbesCoefficient`):
  `n·TP / (|A|·|B|)`, both integers converted to doubles once, then one division. Records as
  for the Jaccard index; either with no 1 is an error. **(implemented)**
- **McConnaughey coefficient** ([ADR 0436](adr/0436-mcconnaughey-coefficient.md);
  `mcconnaughey_coefficient(truth, decision)`, C# `Measurements.McConnaugheyCoefficient`):
  `(TP² − FN·FP) / (|A|·|B|)`, both integers converted to doubles once, then one division.
  Records as for the Jaccard index; either with no 1 is an error. **(implemented)**
- **Dennis coefficient** ([ADR 0437](adr/0437-dennis-coefficient.md);
  `dennis_coefficient(truth, decision)`, C# `Measurements.DennisCoefficient`):
  `(TP·TN − FN·FP) / √(n·|A|·|B|)`, both integers converted to doubles once, the
  denominator rooted once, then one division. Records as for the Jaccard index; either with
  no 1 is an error. **(implemented)**
- **Fager-McGowan coefficient** ([ADR 0438](adr/0438-fager-mcgowan-coefficient.md);
  `fager_mcgowan_coefficient(truth, decision)`, C# `Measurements.FagerMcGowanCoefficient`):
  `TP / √(|A|·|B|) − 1 / (2·√max(|A|, |B|))`, each root taken once, evaluated in that
  order. Records as for the Jaccard index; either with no 1 is an error. **(implemented)**
- **Gilbert skill score** ([ADR 0439](adr/0439-gilbert-skill-score.md);
  `gilbert_skill_score(truth, decision)`, C# `Measurements.GilbertSkillScore`):
  `(n·TP − |A|·|B|) / (n·(TP + FN + FP) − |A|·|B|)`, both exact integers converted to
  doubles once, then one division. Records as for the Jaccard index; a zero denominator
  (equal constant records) is an error. **(implemented)**
- **Braun-Blanquet coefficient** ([ADR 0440](adr/0440-braun-blanquet-coefficient.md);
  `braun_blanquet_coefficient(truth, decision)`, C# `Measurements.BraunBlanquetCoefficient`):
  `TP / max(|A|, |B|)`, one division of the counts. Records as for the Jaccard index; both
  with no 1 is an error, one with no 1 gives 0. **(implemented)**
- **Loevinger's H** ([ADR 0441](adr/0441-loevinger-h.md); `loevinger_h(truth, decision)`,
  C# `Measurements.LoevingerH`): `(n·TP − |A|·|B|) / (n·min(|A|, |B|) − |A|·|B|)`, both
  exact integers converted to doubles once, then one division. Records as for the Jaccard
  index; a constant record (a zero denominator) is an error. **(implemented)**
- **Michael's coefficient** ([ADR 0442](adr/0442-michael-coefficient.md);
  `michael_coefficient(truth, decision)`, C# `Measurements.MichaelCoefficient`):
  `4·(TP·TN − FN·FP) / ((TP + TN)² + (FN + FP)²)`, both exact integers converted to doubles
  once, then one division. Records as for the Jaccard index; no other error, since the
  denominator is at least `n²/2`. **(implemented)**
- **Pearson-Heron II coefficient** ([ADR 0443](adr/0443-pearson-heron-ii.md);
  `pearson_heron_ii(truth, decision)`, C# `Measurements.PearsonHeronII`):
  `cos(π·√y / (√x + √y))`, `x` and `y` as for Yule's Q, each converted to a double once and
  rooted once, then `π·sy`, the division and the cosine in that order. Rules as for Yule's
  Q. **(implemented)**
- **Digby's H** ([ADR 0444](adr/0444-digby-h.md); `digby_h(truth, decision)`, C#
  `Measurements.DigbyH`): `(x^(3/4) − y^(3/4)) / (x^(3/4) + y^(3/4))`, `x` and `y` as for
  Yule's Q, each converted to a double once; `v^(3/4)` is `√v · √√v` from correctly rounded
  square roots, never a general power. Rules as for Yule's Q. **(implemented)**
- **Cole's coefficient** ([ADR 0445](adr/0445-cole-coefficient.md);
  `cole_coefficient(truth, decision)`, C# `Measurements.ColeCoefficient`): `Δ = n·TP −
  |A|·|B|` over `n·min(|A|, |B|) − |A|·|B|` when `Δ ≥ 0`, else over
  `|A|·|B| − n·max(0, |A| + |B| − n)`; both exact integers converted to doubles once, then
  one division. Records as for the Jaccard index; a constant record is an error.
  **(implemented)**
- **Anderberg's D** ([ADR 0446](adr/0446-anderberg-d.md); `anderberg_d(truth, decision)`,
  C# `Measurements.AnderbergD`): `(σ − σ') / (2n)` with `σ = max(TP, FN) + max(FP, TN) +
  max(TP, FP) + max(FN, TN)` and `σ' = max(|A|, n − |A|) + max(|B|, n − |B|)`; both exact
  integers converted to doubles once, then one division. Records as for the Jaccard index;
  no other error. **(implemented)**
- **Goodman and Kruskal's lambda** ([ADR 0447](adr/0447-goodman-kruskal-lambda.md);
  `goodman_kruskal_lambda(truth, decision)`, C# `Measurements.GoodmanKruskalLambda`): the
  symmetric lambda `(σ − σ') / (2n − σ')`, `σ` and `σ'` as for Anderberg's D; both exact
  integers converted to doubles once, then one division. Records as for the Jaccard index;
  `σ' = 2n` (both records constant) is an error. **(implemented)**
- **The Austin-Colwell coefficient** ([ADR 0448](adr/0448-austin-colwell-coefficient.md);
  `austin_colwell_coefficient(truth, decision)`, C#
  `Measurements.AustinColwellCoefficient`): `p = (TP + TN)/n` from exact integers converted
  to doubles once, then `asin(√p) · 2 / π` in that order. Records as for the Jaccard index;
  no other error. **(implemented)**
- **Fossum's coefficient** ([ADR 0449](adr/0449-fossum-coefficient.md);
  `fossum_coefficient(truth, decision)`, C# `Measurements.FossumCoefficient`):
  `n·(2·TP − 1)² / (4·|A|·|B|)`, both exact integers converted to doubles once, then one
  division. Records as for the Jaccard index; a record with no 1 is an error.
  **(implemented)**
- **Eyraud's coefficient** ([ADR 0450](adr/0450-eyraud-coefficient.md);
  `eyraud_coefficient(truth, decision)`, C# `Measurements.EyraudCoefficient`):
  `c · n² / (u · v)` with `c = n·TP − |A|·|B|`, `u = |A|·|B|`, `v = (n − |A|)·(n − |B|)`,
  each exact integer converted to a double once, the operations in that order. Records as
  for the Jaccard index; a constant record is an error. **(implemented)**
- **Stiles' coefficient** ([ADR 0451](adr/0451-stiles-coefficient.md);
  `stiles_coefficient(truth, decision)`, C# `Measurements.StilesCoefficient`):
  `log10(n · e · e / (4 · u · v))` with `e = 2·|n·TP − |A|·|B|| − n`, `u = |A|·|B|`,
  `v = (n − |A|)·(n − |B|)`, each exact integer converted to a double once, the operations in
  that order. Records as for the Jaccard index; a constant record or `e = 0` is an error.
  **(implemented)**
- **Mountford's coefficient** ([ADR 0452](adr/0452-mountford-coefficient.md);
  `mountford_coefficient(truth, decision)`, C# `Measurements.MountfordCoefficient`):
  `2·TP / (TP·FN + TP·FP + 2·FN·FP)`, both exact integers converted to doubles once, then
  one division. Records as for the Jaccard index; a zero denominator is an error.
  **(implemented)**
- **Tarwid's coefficient** ([ADR 0453](adr/0453-tarwid-coefficient.md);
  `tarwid_coefficient(truth, decision)`, C# `Measurements.TarwidCoefficient`):
  `(n·TP − |A|·|B|) / (n·TP + |A|·|B|)`, both exact integers converted to doubles once,
  then one division. Records as for the Jaccard index; a record with no 1 is an error.
  **(implemented)**
- **The Hawkins-Dotson coefficient** ([ADR 0454](adr/0454-hawkins-dotson-coefficient.md);
  `hawkins_dotson_coefficient(truth, decision)`, C# `Measurements.HawkinsDotsonCoefficient`):
  with `m = FN + FP`, `(TP·(TN + m) + TN·(TP + m)) / (2·(TP + m)·(TN + m))`, both exact
  integers converted to doubles once, then one division. Records as for the Jaccard index;
  a zero denominator (both records all 0, or both all 1) is an error. **(implemented)**
- **The Gower-Legendre coefficient** ([ADR 0455](adr/0455-gower-legendre-coefficient.md);
  `gower_legendre_coefficient(truth, decision)`, C# `Measurements.GowerLegendreCoefficient`):
  `2·(TP + TN) / (2·(TP + TN) + FN + FP)`, both exact integers converted to doubles once,
  then one division. Records as for the Jaccard index; no other error, since the
  denominator is at least `n`. **(implemented)**
- **Faith's coefficient** ([ADR 0456](adr/0456-faith-coefficient.md);
  `faith_coefficient(truth, decision)`, C# `Measurements.FaithCoefficient`):
  `(2·TP + TN) / (2·n)`, both exact integers converted to doubles once, then one division.
  Records as for the Jaccard index; no other error. **(implemented)**
- **The Consonni-Todeschini coefficient**
  ([ADR 0457](adr/0457-consonni-todeschini-coefficient.md);
  `consonni_todeschini_coefficient(truth, decision)`, C#
  `Measurements.ConsonniTodeschiniCoefficient`): `ln(1 + TP + TN) / ln(1 + n)`, both exact
  integers converted to doubles once, the platform's natural `log` of each, then one
  division. Records as for the Jaccard index; no other error. **(implemented)**
- **The Maxwell-Pilliner coefficient**
  ([ADR 0458](adr/0458-maxwell-pilliner-coefficient.md);
  `maxwell_pilliner_coefficient(truth, decision)`, C#
  `Measurements.MaxwellPillinerCoefficient`): `2·(TP·TN − FN·FP) / (|A|·(n − |A|) +
  |B|·(n − |B|))`, both exact integers converted to doubles once, then one division.
  Records as for the Jaccard index; both records constant is an error. **(implemented)**
- **The fourth Sokal-Sneath coefficient** ([ADR 0459](adr/0459-sokal-sneath-iv.md);
  `sokal_sneath_iv(truth, decision)`, C# `Measurements.SokalSneathIV`): the mean of
  `TP/|A|`, `TP/|B|`, `TN/(n − |A|)` and `TN/(n − |B|)`, each quotient of exact integers
  converted to doubles once, summed in that order, then divided by 4. Records as for the
  Jaccard index; a constant record is an error. **(implemented)**
- **The fifth Sokal-Sneath coefficient** ([ADR 0460](adr/0460-sokal-sneath-v.md);
  `sokal_sneath_v(truth, decision)`, C# `Measurements.SokalSneathV`): `TP·TN / sqrt(u · v)`
  with `u = |A|·|B|` and `v = (n − |A|)·(n − |B|)`, each exact integer converted to a double
  once. Records as for the Jaccard index; a constant record is an error. **(implemented)**
- **The third Sokal-Sneath coefficient** ([ADR 0461](adr/0461-sokal-sneath-iii.md);
  `sokal_sneath_iii(truth, decision)`, C# `Measurements.SokalSneathIII`):
  `(TP + TN) / (FN + FP)`, both exact integers converted to doubles once, then one
  division. Records as for the Jaccard index; `FN + FP = 0` is an error. **(implemented)**
- **The first Kulczynski coefficient** ([ADR 0462](adr/0462-kulczynski-i.md);
  `kulczynski_i(truth, decision)`, C# `Measurements.KulczynskiI`):
  `TP / (FN + FP)`, both exact integers converted to doubles once, then one
  division. Records as for the Jaccard index; `FN + FP = 0` is an error. **(implemented)**
- **Gilbert-Wells coefficient** ([ADR 0463](adr/0463-gilbert-wells-coefficient.md);
  `gilbert_wells_coefficient(truth, decision)`, C# `Measurements.GilbertWellsCoefficient`):
  `ln(n·TP / (|A|·|B|))`, the exact integers `n·TP` and `|A|·|B|` converted to doubles once,
  one division, then the platform's natural `log`. Records as for the Jaccard index;
  `TP = 0` is an error. **(implemented)**
- **Binary mutual information** ([ADR 0464](adr/0464-binary-mutual-information.md);
  `binary_mutual_information(truth, decision)`, C# `Measurements.BinaryMutualInformation`):
  in nats, the terms `(c/n)·ln(n·c / (r·k))` for the nonzero cells in the order TP, FN, FP,
  TN, each with its truth margin `r` and decision margin `k`, every exact integer converted
  to a double once and the platform's natural `log` used; summed in that order from 0.
  Records as for the Jaccard index; no other error. **(implemented)**
- **Benini coefficient** ([ADR 0465](adr/0465-benini-coefficient.md);
  `benini_coefficient(truth, decision)`, C# `Measurements.BeniniCoefficient`):
  `(n·TP − |A|·|B|) / (n·min(|A|, |B|) − |A|·|B|)`, both exact integers converted to
  doubles once, then one division. Records as for the Jaccard index; a denominator of 0
  (a record with no 1, or all 1) is an error. **(implemented)**
- **Doolittle coefficient** ([ADR 0466](adr/0466-doolittle-coefficient.md);
  `doolittle_coefficient(truth, decision)`, C# `Measurements.DoolittleCoefficient`):
  `(x·x) / (u·v)` in doubles, with the exact integers `x = n·TP − |A|·|B|`,
  `u = |A|·|B|` and `v = (n − |A|)·(n − |B|)` each converted to a double once. Records as
  for the Jaccard index; a constant record is an error. **(implemented)**
- **Rogot-Goldberg coefficient** ([ADR 0467](adr/0467-rogot-goldberg-coefficient.md);
  `rogot_goldberg_coefficient(truth, decision)`, C# `Measurements.RogotGoldbergCoefficient`):
  `TP/(2·TP + FN + FP) + TN/(2·TN + FN + FP)`, each quotient of exact integers converted to
  doubles once, added in that order. Records as for the Jaccard index; both records all 0
  or both all 1 is an error. **(implemented)**
- **The second Baroni-Urbani-Buser coefficient** ([ADR 0468](adr/0468-baroni-urbani-buser-ii.md);
  `baroni_urbani_buser_ii(truth, decision)`, C# `Measurements.BaroniUrbaniBuserII`):
  `(r + (TP − FN − FP)) / (r + (TP + FN + FP))` with `r = √(TP·TN)`, the integer product
  converted to a double once and rooted once, each bracketed integer converted to a double
  once. Records as for the Jaccard index; both all 0 is an error. **(implemented)**
- **Gower's coefficient** ([ADR 0469](adr/0469-gower-coefficient.md);
  `gower_coefficient(truth, decision)`, C# `Measurements.GowerCoefficient`):
  `(TP + TN) / sqrt(u · v)` with `u = |A|·|B|` and `v = (n − |A|)·(n − |B|)`, each exact
  integer converted to a double once. Records as for the Jaccard index; a constant record
  is an error. **(implemented)**
- **Johnson coefficient** ([ADR 0470](adr/0470-johnson-coefficient.md);
  `johnson_coefficient(truth, decision)`, C# `Measurements.JohnsonCoefficient`):
  `TP/|A| + TP/|B|`, each quotient of exact integers converted to doubles once, added in
  that order. Records as for the Jaccard index; a record with no 1 is an error.
  **(implemented)**
- **Dispersion coefficient** ([ADR 0471](adr/0471-dispersion-coefficient.md);
  `dispersion_coefficient(truth, decision)`, C# `Measurements.DispersionCoefficient`):
  `(TP·TN − FN·FP) / n²`, the two exact integers each converted to a double once. Records
  as for the Jaccard index; constant records give 0. **(implemented)**
- **Size difference** ([ADR 0472](adr/0472-size-difference.md);
  `size_difference(truth, decision)`, C# `Measurements.SizeDifference`):
  `(FN + FP)² / n²`, the two exact integers each converted to a double once. Records as for
  the Jaccard index; constant records are allowed. **(implemented)**
- **Shape difference** ([ADR 0473](adr/0473-shape-difference.md);
  `shape_difference(truth, decision)`, C# `Measurements.ShapeDifference`):
  `(n·(FN + FP) − (FN − FP)²) / n²`, the two exact integers each converted to a double once.
  Records as for the Jaccard index; constant records are allowed. **(implemented)**
- **Pattern difference** ([ADR 0474](adr/0474-pattern-difference.md);
  `pattern_difference(truth, decision)`, C# `Measurements.PatternDifference`):
  `4·FN·FP / n²`, the two exact integers each converted to a double once. Records as for
  the Jaccard index; constant records are allowed. **(implemented)**
- **Variance dissimilarity** ([ADR 0475](adr/0475-variance-dissimilarity.md);
  `variance_dissimilarity(truth, decision)`, C# `Measurements.VarianceDissimilarity`):
  `(FN + FP) / (4·n)`, the two exact integers each converted to a double once. Records as
  for the Jaccard index; constant records are allowed. **(implemented)**
- **Lance-Williams distance** ([ADR 0476](adr/0476-lance-williams-distance.md);
  `lance_williams_distance(truth, decision)`, C# `Measurements.LanceWilliamsDistance`):
  `(FN + FP) / (2·TP + FN + FP)`, the two exact integers each converted to a double once.
  Records as for the Jaccard index; both all 0 is an error. **(implemented)**
- **Chord distance of two binary records** ([ADR 0477](adr/0477-chord-distance.md);
  `chord_distance(truth, decision)`, C# `Measurements.ChordDistance`): `sqrt(2·(1 − o))`
  with `o = TP / sqrt(|A|·|B|)`, `TP` and `|A|·|B|` exact integers each converted to a
  double once. Records as for the Jaccard index; a record with no 1 is an error.
  **(implemented)**
- **Chi-square statistic of two binary records** ([ADR 0478](adr/0478-binary-chi-square.md);
  `binary_chi_square(truth, decision)`, C# `Measurements.BinaryChiSquare`): `n · phi · phi`
  with `phi = (TP·TN − FN·FP) / sqrt(u · v)`, `u = |A|·|B|`, `v = (n − |A|)·(n − |B|)`, each
  exact integer converted to a double once. No continuity correction. Records as for the
  Jaccard index; a constant record is an error. **(implemented)**
- **McNemar's statistic** ([ADR 0479](adr/0479-mcnemar-statistic.md);
  `mcnemar_statistic(truth, decision)`, C# `Measurements.McNemarStatistic`):
  `(FN − FP)² / (FN + FP)`, the two exact integers each converted to a double once; no
  continuity correction. Records as for the Jaccard index; records that agree everywhere
  are an error. **(implemented)**
- **Log odds ratio** ([ADR 0480](adr/0480-log-odds-ratio.md);
  `log_odds_ratio(truth, decision)`, C# `Measurements.LogOddsRatio`):
  `ln(TP·TN / (FN·FP))`, the exact integers `TP·TN` and `FN·FP` converted to doubles once,
  one division, then the platform's natural `log`; no cell correction. Records as for the
  Jaccard index; a zero cell is an error. **(implemented)**
- **G statistic of two binary records** ([ADR 0481](adr/0481-binary-g-statistic.md);
  `binary_g_statistic(truth, decision)`, C# `Measurements.BinaryGStatistic`):
  `2·Σ c·ln(n·c / (r·k))` over the nonzero cells `c` with row total `r` and column total
  `k`, the exact integers converted to doubles once, the cells added in the order TP, FN,
  FP, TN, then doubled; not clamped at 0. Records as for the Jaccard index; constant
  records are allowed. **(implemented)**
- **Positive likelihood ratio** ([ADR 0482](adr/0482-positive-likelihood-ratio.md);
  `positive_likelihood_ratio(truth, decision)`, C# `Measurements.PositiveLikelihoodRatio`):
  `TP·(FP + TN) / (|A|·FP)`, the two exact integers each converted to a double once, then
  one division. Records as for the Jaccard index; truth with no 1, or `FP = 0`, is an
  error. **(implemented)**
- **Negative likelihood ratio** ([ADR 0483](adr/0483-negative-likelihood-ratio.md);
  `negative_likelihood_ratio(truth, decision)`, C# `Measurements.NegativeLikelihoodRatio`):
  `FN·(FP + TN) / (|A|·TN)`, the two exact integers each converted to a double once, then
  one division. Records as for the Jaccard index; truth with no 1, or `TN = 0`, is an
  error. **(implemented)**
- **Relative risk** ([ADR 0484](adr/0484-relative-risk.md);
  `relative_risk(truth, decision)`, C# `Measurements.RelativeRisk`): the decision as the
  exposure, `TP·(FN + TN) / ((TP + FP)·FN)`, the two exact integers each converted to a
  double once, then one division. Records as for the Jaccard index; a decision with no 1,
  or `FN = 0`, is an error. **(implemented)**
- **Attributable fraction** ([ADR 0485](adr/0485-attributable-fraction.md);
  `attributable_fraction(truth, decision)`, C# `Measurements.AttributableFraction`): the
  decision as the exposure, `(TP·(FN + TN) − FN·(TP + FP)) / (TP·(FN + TN))`, the two
  exact integers each converted to a double once, then one division. Records as for the
  Jaccard index; `TP = 0`, or a decision with no 0, is an error. **(implemented)**
- **Population attributable fraction**
  ([ADR 0486](adr/0486-population-attributable-fraction.md);
  `population_attributable_fraction(truth, decision)`, C#
  `Measurements.PopulationAttributableFraction`): the decision as the exposure,
  `(u − n·FN) / u` with `u = |A|·(FN + TN)`, the two exact integers each converted to a
  double once, then one division. Records as for the Jaccard index; truth with no 1, or a
  decision with no 0, is an error. **(implemented)**
- **Prevalence threshold** ([ADR 0487](adr/0487-prevalence-threshold.md);
  `prevalence_threshold(truth, decision)`, C# `Measurements.PrevalenceThreshold`):
  `(sqrt(TP·FP·a·b) − FP·a) / (TP·b − FP·a)` with `a = |A|`, `b = n − |A|`; `TP·FP` and
  `a·b` each converted to a double once and multiplied before the square root, `FP·a` and
  `TP·b − FP·a` each converted once. Records as for the Jaccard index; a constant truth, or
  `TP·b = FP·a`, is an error. **(implemented)**
- **Frequency bias** ([ADR 0488](adr/0488-frequency-bias.md);
  `frequency_bias(truth, decision)`, C# `Measurements.FrequencyBias`): `|B| / |A|`, the
  two exact counts each converted to a double once, then one division. Records as for the
  Jaccard index; truth with no 1 is an error. **(implemented)**
- **Extreme dependency score** ([ADR 0489](adr/0489-extreme-dependency-score.md);
  `extreme_dependency_score(truth, decision)`, C# `Measurements.ExtremeDependencyScore`):
  `2·ln(|A| / n) / ln(TP / n) − 1`, the counts each converted to a double once and each
  logarithm taken of one division. Records as for the Jaccard index; `TP = 0`, or
  `TP = n`, is an error. **(implemented)**
- **Extremal dependence index** ([ADR 0490](adr/0490-extremal-dependence-index.md);
  `extremal_dependence_index(truth, decision)`, C# `Measurements.ExtremalDependenceIndex`):
  `(ln F − ln H) / (ln F + ln H)` with `H = TP / |A|`, `F = FP / (n − |A|)`, the counts each
  converted to a double once and each logarithm taken of one division. Records as for the
  Jaccard index; a constant truth, `TP = 0`, `FP = 0`, or a decision of all 1 is an error.
  **(implemented)**
- **Symmetric extremal dependence index**
  ([ADR 0491](adr/0491-symmetric-extremal-dependence-index.md);
  `symmetric_extremal_dependence_index(truth, decision)`, C#
  `Measurements.SymmetricExtremalDependenceIndex`):
  `(ln F − ln H − ln(1 − F) + ln(1 − H)) / (ln F + ln H + ln(1 − F) + ln(1 − H))` with
  `H = TP / |A|`, `F = FP / (n − |A|)`; each logarithm taken of one division of two counts,
  each converted to a double once, the sums left to right. Records as for the Jaccard
  index; any cell equal to 0 is an error. **(implemented)**
- **Tetrachoric approximation** ([ADR 0492](adr/0492-tetrachoric-approximation.md);
  `tetrachoric_approximation(truth, decision)`, C#
  `Measurements.TetrachoricApproximation`): Pearson's `cos(π / (1 + sqrt(TP·TN / (FN·FP))))`;
  `TP·TN` and `FN·FP` each converted to a double once, then the division, the square root,
  `1 +`, π divided by the sum, and the cosine. Records as for the Jaccard index;
  `FN·FP = 0` is an error. **(implemented)**
- **Standard error of the log odds ratio**
  ([ADR 0493](adr/0493-log-odds-ratio-standard-error.md);
  `log_odds_ratio_standard_error(truth, decision)`, C#
  `Measurements.LogOddsRatioStandardError`): Woolf's `sqrt(1/TP + 1/FN + 1/FP + 1/TN)`,
  formed as one exact rational whose numerator and denominator are each converted to a
  double once, then one division and the square root. Records as for the Jaccard index;
  any cell equal to 0 is an error. **(implemented)**
- **Haldane log odds ratio** ([ADR 0494](adr/0494-haldane-log-odds-ratio.md);
  `haldane_log_odds_ratio(truth, decision)`, C# `Measurements.HaldaneLogOddsRatio`):
  `ln((2·TP + 1)(2·TN + 1) / ((2·FN + 1)(2·FP + 1)))`, a half added to every cell; the two
  exact integers each converted to a double once, then one division and the logarithm.
  Records as for the Jaccard index; no other errors. **(implemented)**
- **Standard error of Yule's Q** ([ADR 0495](adr/0495-yule-q-standard-error.md);
  `yule_q_standard_error(truth, decision)`, C# `Measurements.YuleQStandardError`):
  `½·(1 − Q²)·sqrt(1/TP + 1/FN + 1/FP + 1/TN)`, formed as `2·sqrt(xy·N) / (x + y)²` with
  `x = TP·TN`, `y = FN·FP`, `N` the numerator of the reciprocal sum; `xy`, `N` and `x + y`
  each converted to a double once. Records as for the Jaccard index; any cell equal to 0
  is an error. **(implemented)**
- **Standard error of Yule's Y** ([ADR 0496](adr/0496-yule-y-standard-error.md);
  `yule_y_standard_error(truth, decision)`, C# `Measurements.YuleYStandardError`):
  `¼·(1 − Y²)·sqrt(1/TP + 1/FN + 1/FP + 1/TN)`, formed as `√N / (√x + √y)²` with
  `x = TP·TN`, `y = FN·FP`, `N` the numerator of the reciprocal sum; `N`, `x` and `y` each
  converted to a double once. Records as for the Jaccard index; any cell equal to 0 is an
  error. **(implemented)**
- **Standard error of the Haldane log odds ratio**
  ([ADR 0497](adr/0497-haldane-log-odds-ratio-standard-error.md);
  `haldane_log_odds_ratio_standard_error(truth, decision)`, C#
  `Measurements.HaldaneLogOddsRatioStandardError`): `sqrt(Σ 1/(cell + ½))`, formed with
  `a..d = 2·cell + 1` as the exact rational `2·(bcd + acd + abd + abc) / (abcd)` whose
  numerator and denominator are each converted to a double once. Records as for the
  Jaccard index; no other errors. **(implemented)**
- **Wald z of the log odds ratio** ([ADR 0498](adr/0498-log-odds-ratio-wald-z.md);
  `log_odds_ratio_wald_z(truth, decision)`, C# `Measurements.LogOddsRatioWaldZ`): the log
  odds ratio over its standard error, formed as `ln(x/y)·sqrt(xy / N)` with `x = TP·TN`,
  `y = FN·FP`, `N` the numerator of the reciprocal sum; `x`, `y`, `xy` and `N` each
  converted to a double once. Records as for the Jaccard index; any cell equal to 0 is an
  error. **(implemented)**
- **Standard error of the log relative risk**
  ([ADR 0499](adr/0499-log-relative-risk-standard-error.md);
  `log_relative_risk_standard_error(truth, decision)`, C#
  `Measurements.LogRelativeRiskStandardError`): `sqrt(1/TP − 1/(TP + FP) + 1/FN −
  1/(FN + TN))`, formed as the exact rational
  `(FP·FN·(FN + TN) + TN·TP·(TP + FP)) / (TP·(TP + FP)·FN·(FN + TN))` whose numerator and
  denominator are each converted to a double once. Records as for the Jaccard index;
  TP = 0 or FN = 0 is an error. **(implemented)**
- **Wald z of the log relative risk** ([ADR 0500](adr/0500-log-relative-risk-wald-z.md);
  `log_relative_risk_wald_z(truth, decision)`, C# `Measurements.LogRelativeRiskWaldZ`):
  the log relative risk over its standard error, formed as `ln(P/Q)·sqrt(PQ / M)` with
  `P = TP·(FN + TN)`, `Q = FN·(TP + FP)` and `M = FP·FN·(FN + TN) + TN·TP·(TP + FP)`; each
  exact integer converted to a double once. Records as for the Jaccard index; TP = 0,
  FN = 0 or `M = 0` is an error. **(implemented)**
- **Risk difference** ([ADR 0501](adr/0501-risk-difference.md);
  `risk_difference(truth, decision)`, C# `Measurements.RiskDifference`), the decision as
  the exposure: `TP/(TP + FP) − FN/(FN + TN)`, formed as
  `(TP·TN − FN·FP) / ((TP + FP)·(FN + TN))` with the two exact integers each converted to
  a double once. Records as for the Jaccard index; a decision with no 1 or no 0 is an
  error. **(implemented)**
- **Standard error of the risk difference**
  ([ADR 0502](adr/0502-risk-difference-standard-error.md);
  `risk_difference_standard_error(truth, decision)`, C#
  `Measurements.RiskDifferenceStandardError`), the decision as the exposure:
  `sqrt(TP·FP/(TP + FP)³ + FN·TN/(FN + TN)³)`, each term an exact integer over an exact
  integer, each converted to a double once. Records as for the Jaccard index; a decision
  with no 1 or no 0 is an error. **(implemented)**
- **Wald z of the risk difference** ([ADR 0503](adr/0503-risk-difference-wald-z.md);
  `risk_difference_wald_z(truth, decision)`, C# `Measurements.RiskDifferenceWaldZ`), the
  decision as the exposure: the risk difference, formed as for ADR 0501, over the square
  root of its squared standard error, formed as for ADR 0502. Records as for the Jaccard
  index; a decision with no 1 or no 0, or a standard error of 0, is an error.
  **(implemented)**
- **Number needed to treat** ([ADR 0504](adr/0504-number-needed-to-treat.md);
  `number_needed_to_treat(truth, decision)`, C# `Measurements.NumberNeededToTreat`), the
  decision as the exposure: the reciprocal of the risk difference, formed as
  `(TP + FP)·(FN + TN) / (TP·TN − FN·FP)` with the two exact integers each converted to a
  double once. Records as for the Jaccard index; a decision with no 1 or no 0, or a risk
  difference of 0, is an error. **(implemented)**
- **Relative risk reduction** ([ADR 0505](adr/0505-relative-risk-reduction.md);
  `relative_risk_reduction(truth, decision)`, C# `Measurements.RelativeRiskReduction`),
  the decision as the exposure: one minus the relative risk, formed as
  `(FN·FP − TP·TN) / ((TP + FP)·FN)` with the two exact integers each converted to a
  double once. Records as for the Jaccard index; a decision with no 1, or `FN = 0`, is an
  error. **(implemented)**
- **Cohen's h** ([ADR 0506](adr/0506-cohen-h.md); `cohen_h(truth, decision)`, C#
  `Measurements.CohenH`), the decision as the exposure:
  `2·asin(√(TP/(TP + FP))) − 2·asin(√(FN/(FN + TN)))`, formed as
  `2·(atan2(√TP, √FP) − atan2(√FN, √TN))`; from −π to π. Records as for the Jaccard
  index; a decision with no 1 or no 0 is an error. **(implemented)**
- **Standard error of Cohen's h** ([ADR 0507](adr/0507-cohen-h-standard-error.md);
  `cohen_h_standard_error(truth, decision)`, C# `Measurements.CohenHStandardError`), the
  decision as the exposure: `√(1/(TP + FP) + 1/(FN + TN))`, formed as the exact integer
  `N` over the exact integer `(TP + FP)·(FN + TN)`, each converted to a double once.
  Records as for the Jaccard index; a decision with no 1 or no 0 is an error.
  **(implemented)**
- **Wald z of Cohen's h** ([ADR 0508](adr/0508-cohen-h-wald-z.md);
  `cohen_h_wald_z(truth, decision)`, C# `Measurements.CohenHWaldZ`), the decision as the
  exposure: Cohen's h, formed as for ADR 0506, over the square root of its squared
  standard error, formed as for ADR 0507. Records as for the Jaccard index; a decision
  with no 1 or no 0 is an error. **(implemented)**
- **Log relative risk** ([ADR 0509](adr/0509-log-relative-risk.md);
  `log_relative_risk(truth, decision)`, C# `Measurements.LogRelativeRisk`): the decision as the
  exposure, `ln(P/Q)` with `P = TP·(FN + TN)` and `Q = FN·(TP + FP)`, each exact integer
  converted to a double once. Records as for the Jaccard index; TP = 0 or FN = 0 is an
  error. **(implemented)**
- **Inequality records, scaled first** ([ADR 0626](adr/0626-inequality-records-scaled-first.md)):
  the Gini, Theil, Hoover, Atkinson, generalized entropy, Bonferroni, Zenga and Wolfson
  indices, the mean log deviation, the coefficient of variation, the Lorenz curve, and the
  Palma and quintile share ratios divide the checked record by its largest value, when that
  is positive, before forming any sum, so no sum overflows. **(implemented)**
- **Gini coefficient** ([ADR 0510](adr/0510-gini-coefficient.md);
  `gini_coefficient(samples)`, C# `Measurements.GiniCoefficient`): the population form
  `Σᵢ Σⱼ |xᵢ − xⱼ| / (2·n²·μ)` over all `n²` ordered pairs, computed on the sorted values
  as `Σₖ (2k − n + 1)·x₍ₖ₎ / (n·Σ x)`, `k` from 0. From 0 to `1 − 1/n`. Real, finite,
  `n ≥ 1`, every value at least 0, not all 0. **(implemented)**
- **Theil index** ([ADR 0511](adr/0511-theil-index.md); `theil_index(samples)`, C#
  `Measurements.TheilIndex`): `(1/n)·Σ (xᵢ/μ)·ln(xᵢ/μ)`, `μ` the mean, a term with
  `xᵢ = 0` taken as 0. From 0 to `ln n`. Records as for the Gini coefficient: real,
  finite, `n ≥ 1`, every value at least 0, not all 0. **(implemented)**
- **Hoover index** ([ADR 0512](adr/0512-hoover-index.md); `hoover_index(samples)`, C#
  `Measurements.HooverIndex`): `Σ |xᵢ − μ| / (2·Σ xᵢ)`, `μ` the mean. From 0 to
  `1 − 1/n`. Records as for the Gini coefficient: real, finite, `n ≥ 1`, every value at
  least 0, not all 0. **(implemented)**
- **Coefficient of variation** ([ADR 0513](adr/0513-coefficient-of-variation.md);
  `coefficient_of_variation(samples)`, C# `Measurements.CoefficientOfVariation`): `σ/μ`,
  `σ` the population standard deviation, over `n`, `μ` the mean. Real, finite, `n ≥ 1`,
  the mean greater than 0; values below 0 allowed. **(implemented)**
- **Mean log deviation** ([ADR 0514](adr/0514-mean-log-deviation.md);
  `mean_log_deviation(samples)`, C# `Measurements.MeanLogDeviation`):
  `(1/n)·Σ ln(μ/xᵢ)`, `μ` the mean, each term the log of the ratio. At least 0. Real,
  finite, `n ≥ 1`, every value greater than 0. **(implemented)**
- **Atkinson index** ([ADR 0515](adr/0515-atkinson-index.md);
  `atkinson_index(samples, epsilon)`, C# `Measurements.AtkinsonIndex`): with `rᵢ = xᵢ/μ`,
  `1 − ((1/n)·Σ rᵢ^(1−ε))^(1/(1−ε))` for `ε ≠ 1`, `1 − exp((1/n)·Σ ln rᵢ)` at `ε = 1`.
  From 0 to below 1. Real, finite, `n ≥ 1`, every value greater than 0; `ε` finite, at
  least 0. **(implemented)**
- **Generalized entropy index** ([ADR 0516](adr/0516-generalized-entropy-index.md);
  `generalized_entropy_index(samples, alpha)`, C# `Measurements.GeneralizedEntropyIndex`):
  with `rᵢ = xᵢ/μ`, `(1/(n·α(α − 1)))·Σ (rᵢ^α − 1)`; at exactly `α = 0`,
  `−(1/n)·Σ ln rᵢ`, and at exactly `α = 1`, `(1/n)·Σ rᵢ·ln rᵢ`. At least 0. Real, finite,
  `n ≥ 1`, every value greater than 0; `α` finite. **(implemented)**
- **Lorenz curve** ([ADR 0517](adr/0517-lorenz-curve.md); `lorenz_curve(samples)`, C#
  `Measurements.LorenzCurve`): `n + 1` shares, `L₀ = 0`, `Lₖ = Sₖ/Sₙ`, `Sₖ` the running
  sum of the `k` smallest values added from the smallest; the last share is exactly 1.
  Records as for the Gini coefficient. **(implemented)**
- **Palma ratio** ([ADR 0518](adr/0518-palma-ratio.md); `palma_ratio(samples)`, C#
  `Measurements.PalmaRatio`): `(Sₙ − upto)/low` from the Lorenz curve joined by straight
  lines, `x₍ₖ₎` sorted, `Sₖ` the running sum of the `k` smallest; `2n = 5j₄ + r₄`,
  `low = S_{j₄} + (r₄/5)·x₍j₄₎`; `9n = 10j₉ + r₉`, `upto = S_{j₉} + (r₉/10)·x₍j₉₎`. Real,
  finite, `n ≥ 1`, every value at least 0, `low > 0`. **(implemented)**
- **Quintile share ratio** ([ADR 0519](adr/0519-quintile-share-ratio.md);
  `quintile_share_ratio(samples)`, C# `Measurements.QuintileShareRatio`): `(Sₙ − upto)/low`
  from the Lorenz curve joined by straight lines, as for the Palma ratio;
  `n = 5j₂ + r₂`, `low = S_{j₂} + (r₂/5)·x₍j₂₎`; `4n = 5j₈ + r₈`,
  `upto = S_{j₈} + (r₈/5)·x₍j₈₎`. Real, finite, `n ≥ 1`, every value at least 0,
  `low > 0`. **(implemented)**
- **Bonferroni index** ([ADR 0520](adr/0520-bonferroni-index.md);
  `bonferroni_index(samples)`, C# `Measurements.BonferroniIndex`):
  `(1/(n − 1))·Σ_{k=1}^{n−1} (μ − mₖ)/μ`, `mₖ = Sₖ/k` the mean of the `k` smallest; the
  `k = n` term left out, so from 0 to 1. Formed as `1 − n·Σ_{k<n} (Sₖ/k)/((n − 1)·Sₙ)`,
  summed from `k = 1`. Real, finite, `n ≥ 2`, every value at least 0, not all 0.
  **(implemented)**
- **Zenga index** ([ADR 0521](adr/0521-zenga-index.md); `zenga_index(samples)`, C#
  `Measurements.ZengaIndex`): `(1/(n − 1))·Σ_{k=1}^{n−1} (m⁺ₖ − m⁻ₖ)/m⁺ₖ`, `m⁻ₖ = Sₖ/k`,
  `m⁺ₖ = (Sₙ − Sₖ)/(n − k)`. Formed as `1 − Σ_{k<n} m⁻ₖ/m⁺ₖ/(n − 1)`, summed from
  `k = 1`. Records as for the Bonferroni index. **(implemented)**
- **Wolfson polarization index** ([ADR 0522](adr/0522-wolfson-index.md);
  `wolfson_index(samples)`, C# `Measurements.WolfsonIndex`): `2·(μ/m)·(1 − 2·L(1/2) − G)`,
  `m` the median (`(a + b)/2` for an even count), `L(1/2) = (S_j + (r/2)·x₍ⱼ₎)/Sₙ` for
  `n = 2j + r`, `G` the Gini coefficient. Formed as
  `2·(Sₙ − 2·(S_j + (r/2)·x₍ⱼ₎) − g/n)/(n·m)`, `g = Σₖ (2k − n + 1)·x₍ₖ₎` from `k = 0`.
  Real, finite, `n ≥ 1`, every value at least 0, median above 0. **(implemented)**
- **Shares of a record, scaled first** ([ADR 0625](adr/0625-shares-scaled-before-summing.md)):
  the Herfindahl index, concentration ratio, Hall–Tideman, Kwoka and Hannah–Kay indices,
  Pielou's evenness, the Gini–Simpson and Berger–Parker indices, Heip's, Simpson's, Camargo's,
  Bulla's, Hill ratio, Alatalo's and Sheldon's evenness, and Strong's dominance divide the
  checked record by its largest value before forming the sum and the shares, so no sum
  overflows. **(implemented)**
- **Herfindahl index** ([ADR 0523](adr/0523-herfindahl-index.md);
  `herfindahl_index(samples)`, C# `Measurements.HerfindahlIndex`): `Σᵢ (xᵢ/S)²`, shares as
  fractions, `S` and the squares added in record order; from `1/n` to 1, not normalized.
  Records as for the Gini coefficient. **(implemented)**
- **Concentration ratio** ([ADR 0524](adr/0524-concentration-ratio.md);
  `concentration_ratio(samples, k)`, C# `Measurements.ConcentrationRatio`): the `k` largest
  added from the largest down, over the total added in record order; a fraction. Records
  as for the Gini coefficient; `k` whole, from 1 to `n`. **(implemented)**
- **Hall–Tideman index** ([ADR 0525](adr/0525-hall-tideman-index.md);
  `hall_tideman_index(samples)`, C# `Measurements.HallTidemanIndex`):
  `1/(2·Σ_r r·s₍ᵣ₎ − 1)`, shares ranked from the largest, `r` from 1; formed as
  `S/(2·A − S)`, `A = Σ_r r·x₍ᵣ₎` from the largest down, `S` in record order. Records as for
  the Gini coefficient. **(implemented)**
- **Kwoka dominance index** ([ADR 0526](adr/0526-kwoka-dominance-index.md);
  `kwoka_dominance_index(samples)`, C# `Measurements.KwokaDominanceIndex`):
  `Σ_{r=1}^{n−1} (s₍ᵣ₎ − s₍ᵣ₊₁₎)²`, shares ranked from the largest, every neighbouring pair;
  each gap `(x₍ᵣ₎ − x₍ᵣ₊₁₎)/S`, the squares added from the largest pair down. Records as for
  the Gini coefficient. **(implemented)**
- **Hannah–Kay index** ([ADR 0527](adr/0527-hannah-kay-index.md);
  `hannah_kay_index(samples, alpha)`, C# `Measurements.HannahKayIndex`): the numbers
  equivalent `(Σᵢ sᵢ^α)^(1/(1 − α))`, `exp(−Σᵢ sᵢ ln sᵢ)` at `α = 1` exactly, `0·ln 0 = 0`;
  shares over the total added in record order, the platform `pow`. Records as for the Gini
  coefficient; `α` finite, above 0. **(implemented)**
- **Pielou's evenness** ([ADR 0528](adr/0528-pielou-evenness.md);
  `pielou_evenness(samples)`, C# `Measurements.PielouEvenness`): `−Σᵢ sᵢ ln sᵢ / ln n`,
  `0·ln 0 = 0`, `n` the record length with zero shares counted; terms in record order.
  Real, finite, `n ≥ 2`, every value at least 0, not all 0. **(implemented)**
- **Gini–Simpson index** ([ADR 0529](adr/0529-simpson-diversity.md);
  `simpson_diversity(samples)`, C# `Measurements.SimpsonDiversity`): `1 − Σᵢ sᵢ²`, draws
  with replacement, the complement not the reciprocal; squares in record order, taken from
  1 last. Records as for the Gini coefficient. **(implemented)**
- **Berger–Parker index** ([ADR 0530](adr/0530-berger-parker-index.md);
  `berger_parker_index(samples)`, C# `Measurements.BergerParkerIndex`): `max xᵢ / S`, the
  share not its reciprocal, `S` in record order. Records as for the Gini coefficient.
  **(implemented)**
- **Heip's evenness** ([ADR 0531](adr/0531-heip-evenness.md);
  `heip_evenness(samples)`, C# `Measurements.HeipEvenness`):
  `(exp(−Σᵢ sᵢ ln sᵢ) − 1)/(n − 1)`, `0·ln 0 = 0`, `n` the record length with zero shares
  counted; terms in record order. Records as for Pielou's evenness. **(implemented)**
- **Simpson's evenness** ([ADR 0532](adr/0532-simpson-evenness.md);
  `simpson_evenness(samples)`, C# `Measurements.SimpsonEvenness`): `1/(n·Σᵢ sᵢ²)`, `n` the
  record length with zero shares counted; squares in record order. Records as for the
  Gini coefficient. **(implemented)**
- **Camargo's evenness** ([ADR 0533](adr/0533-camargo-evenness.md);
  `camargo_evenness(samples)`, C# `Measurements.CamargoEvenness`):
  `1 − Σ_{i<j} |sᵢ − sⱼ| / n`, `n` the record length with zero shares counted; gaps over
  `i` in record order then `j > i`, every pair directly. Records as for the Gini
  coefficient. **(implemented)**
- **Smith–Wilson evenness** ([ADR 0534](adr/0534-smith-wilson-evenness.md);
  `smith_wilson_evenness(samples)`, C# `Measurements.SmithWilsonEvenness`):
  `1 − (2/π)·atan(Σᵢ (ln xᵢ − m)²/n)`, `m` the mean of the `ln xᵢ`, divisor `n`; sums in
  record order. Real, finite, at least 1 value, every value above 0. **(implemented)**
- **Bulla's evenness** ([ADR 0535](adr/0535-bulla-evenness.md);
  `bulla_evenness(samples)`, C# `Measurements.BullaEvenness`): `(O − 1/n)/(1 − 1/n)`,
  `O = Σᵢ min(sᵢ, 1/n)`, the rescaled value not `O`; `n` the record length with zero shares
  counted; minima in record order. Records as for Pielou's evenness. **(implemented)**
- **Hill ratio evenness** ([ADR 0536](adr/0536-hill-ratio-evenness.md);
  `hill_ratio_evenness(samples)`, C# `Measurements.HillRatioEvenness`): `E₂,₁ = N₂/N₁`,
  formed as `(1/Σᵢ sᵢ²)/exp(−Σᵢ sᵢ ln sᵢ)`, `0·ln 0 = 0`; both sums in one pass in record
  order. Records as for the Gini coefficient. **(implemented)**
- **Alatalo's evenness** ([ADR 0537](adr/0537-alatalo-evenness.md);
  `alatalo_evenness(samples)`, C# `Measurements.AlataloEvenness`): `(N₂ − 1)/(N₁ − 1)`,
  formed as `(1/Σᵢ sᵢ² − 1)/(exp(−Σᵢ sᵢ ln sᵢ) − 1)`, `0·ln 0 = 0`; both sums in one pass in
  record order. Real, finite, every value at least 0, at least 2 positive shares.
  **(implemented)**
- **Sheldon's evenness** ([ADR 0538](adr/0538-sheldon-evenness.md);
  `sheldon_evenness(samples)`, C# `Measurements.SheldonEvenness`): `exp(−Σᵢ sᵢ ln sᵢ)/n`,
  `0·ln 0 = 0`, `n` the record length with zero shares counted; terms in record order.
  Records as for the Gini coefficient. **(implemented)**
- **McIntosh dominance** ([ADR 0539](adr/0539-mcintosh-dominance.md);
  `mcintosh_dominance(samples)`, C# `Measurements.McIntoshDominance`):
  `(N − U)/(N − √N)`, `N = Σᵢ xᵢ`, `U = √(Σᵢ xᵢ²)`, both sums in record order; depends on
  the scale of the values. Real, finite, every value at least 0, `N > 1`. **(implemented)**
- **McIntosh evenness** ([ADR 0540](adr/0540-mcintosh-evenness.md);
  `mcintosh_evenness(samples)`, C# `Measurements.McIntoshEvenness`):
  `(N − U)/(N − N/√n)`, `N = Σᵢ xᵢ`, `U = √(Σᵢ xᵢ²)`, both sums in record order, `n` the
  record length. At least 2 values, every value at least 0, not all 0. **(implemented)**
- **Menhinick's index** ([ADR 0541](adr/0541-menhinick-index.md);
  `menhinick_index(samples)`, C# `Measurements.MenhinickIndex`): `k/√N`, `k` the count of
  values above 0, `N = Σᵢ xᵢ` in record order. Records as for the Gini coefficient.
  **(implemented)**
- **Margalef's index** ([ADR 0542](adr/0542-margalef-index.md);
  `margalef_index(samples)`, C# `Measurements.MargalefIndex`): `(k − 1)/ln N`, `k` the count
  of values above 0, `N = Σᵢ xᵢ` in record order. Real, finite, every value at least 0,
  `N > 1`. **(implemented)**
- **Gleason's index** ([ADR 0543](adr/0543-gleason-index.md);
  `gleason_index(samples)`, C# `Measurements.GleasonIndex`): `k/ln N`, `k` the count of
  values above 0, `N = Σᵢ xᵢ` in record order. Real, finite, every value at least 0,
  `N > 1`. **(implemented)**
- **Good's coverage** ([ADR 0544](adr/0544-goods-coverage.md);
  `goods_coverage(samples)`, C# `Measurements.GoodsCoverage`): `1 − F₁/N`, `F₁` the count
  of values exactly equal to 1, `N = Σᵢ xᵢ` in record order. Records as for the Gini
  coefficient. **(implemented)**
- **Chao1 richness** ([ADR 0545](adr/0545-chao1-richness.md);
  `chao1_richness(samples)`, C# `Measurements.Chao1Richness`): the bias-corrected
  `k + F₁(F₁ − 1)/(2(F₂ + 1))`, `k` the count of values above 0, `F₁` and `F₂` the counts
  of values exactly 1 and 2. Records as for the Gini coefficient. **(implemented)**
- **Brillouin index** ([ADR 0546](adr/0546-brillouin-index.md);
  `brillouin_index(samples)`, C# `Measurements.BrillouinIndex`): `(ln N! − Σᵢ ln xᵢ!)/N` in
  nats, each `ln m!` the sum of `ln j`, `j = 2 … m` in order; values in record order. Whole
  numbers at least 0, not all 0, `N` at most 10 000 000. **(implemented)**
- **Brillouin evenness** ([ADR 0547](adr/0547-brillouin-evenness.md);
  `brillouin_evenness(samples)`, C# `Measurements.BrillouinEvenness`): the Brillouin index
  over its value for `k − r` counts of `c = ⌊N/k⌋` and `r` of `c + 1`, as
  `(ln N! − Σᵢ ln xᵢ!)/(ln N! − (k − r) ln c! − r ln (c + 1)!)`, the log-factorials as for
  the index. Records as for the index, at least 2 values above 0. **(implemented)**
- **Hurlbert's PIE** ([ADR 0548](adr/0548-hurlbert-pie.md);
  `hurlbert_pie(samples)`, C# `Measurements.HurlbertPie`): `N/(N − 1) · (1 − Σᵢ sᵢ²)`,
  `sᵢ = xᵢ/N`, sums in record order. Real, finite, every value at least 0, `N > 1`.
  **(implemented)**
- **Strong's dominance** ([ADR 0549](adr/0549-strong-dominance.md);
  `strong_dominance(samples)`, C# `Measurements.StrongDominance`): `maxᵢ (bᵢ/N − i/k)`,
  `i = 1 … k`, `bᵢ` the running sum of the positive values largest first, the maximum
  starting at 0. Records as for the Gini coefficient. **(implemented)**
- **Fisher's alpha** ([ADR 0550](adr/0550-fisher-alpha.md);
  `fisher_alpha(samples)`, C# `Measurements.FisherAlpha`): the `α` with
  `α · lp(N/α) = k`, `lp(x)` = `x` when `1 + x = 1`, else `ln(1 + x) · x/((1 + x) − 1)`.
  Search: `lo` halves from 1 while `f(lo) ≥ k`, `hi` doubles from 1 while `f(hi) ≤ k`, then
  100 steps of `mid = √lo · √hi`; the value is `√lo · √hi`. Whole numbers as for the
  Brillouin index, with the total above `k`. **(implemented)**
- **ACE richness** ([ADR 0551](adr/0551-ace-richness.md);
  `ace_richness(samples)`, C# `Measurements.AceRichness`): rare kinds have values 1 to 10;
  `C = 1 − F₁/N_rare`, `γ² = max(S_rare/C · P/(N_rare(N_rare − 1)) − 1, 0)` with
  `P = Σ xᵢ(xᵢ − 1)` over the rare values, `S = S_abund + S_rare/C + F₁/C · γ²`, or
  `S_abund` with no rare kinds. Whole numbers as for the Brillouin index; rare kinds not
  all singletons. **(implemented)**
- **Rarefied richness** ([ADR 0552](adr/0552-rarefied-richness.md);
  `rarefied_richness(samples, size)`, C# `Measurements.RarefiedRichness`):
  `Σᵢ (1 − qᵢ)` over the values above 0, `qᵢ = Πⱼ (N − n − j)/(N − j)` for
  `j = 0 … xᵢ − 1`, stopped once it reaches 0. Whole numbers as for the Brillouin index;
  `size` an integer from 1 to `N`. **(implemented)**
- **Chao–Jost coverage** ([ADR 0553](adr/0553-chao-jost-coverage.md);
  `chao_jost_coverage(samples)`, C# `Measurements.ChaoJostCoverage`): with
  `a = (N − 1)F₁`, `1 − F₁/N · (a/(a + 2F₂))`, or 1 when `F₁ = 0`. Whole numbers as for the
  Brillouin index, with `N > 1`. **(implemented)**
- **Chao–Shen entropy** ([ADR 0554](adr/0554-chao-shen-entropy.md);
  `chao_shen_entropy(samples)`, C# `Measurements.ChaoShenEntropy`): nats;
  `C = 1 − F₁/N` with `F₁ = N` taken as `N − 1`, `aᵢ = C · (xᵢ/N)`, and `H` is 0 less
  `aᵢ ln(aᵢ)/(1 − (1 − aᵢ)^N)` for each value above 0, in record order. Whole numbers as
  for the Brillouin index. **(implemented)**
- **Miller–Madow entropy** ([ADR 0555](adr/0555-miller-madow-entropy.md);
  `miller_madow_entropy(samples)`, C# `Measurements.MillerMadowEntropy`): nats; 0 less
  `pᵢ ln pᵢ` for each value above 0, in record order, plus `(k − 1)/(2N)`. Whole numbers
  as for the Brillouin index. **(implemented)**
- **Hutcheson's variance** ([ADR 0556](adr/0556-hutcheson-variance.md);
  `hutcheson_variance(samples)`, C# `Measurements.HutchesonVariance`): nats²;
  `(Q − L·L)/N + (k − 1)/(2·N·N)`, `L = Σ pᵢ lᵢ` and `Q = Σ pᵢ lᵢ lᵢ` over the values
  above 0 in record order, `lᵢ = ln pᵢ`. Whole numbers as for the Brillouin index.
  **(implemented)**
- **Hutcheson's t** ([ADR 0557](adr/0557-hutcheson-t.md); `hutcheson_t(a, b)`, C#
  `Measurements.HutchesonT`): `(H_a − H_b)/√(V_a + V_b)`, `H = −L` and `V` as for
  Hutcheson's variance; each record as for Hutcheson's variance, and `V_a + V_b > 0`.
  **(implemented)**
- **Jackknife Shannon entropy** ([ADR 0558](adr/0558-jackknife-entropy.md);
  `jackknife_entropy(samples)`, C# `Measurements.JackknifeEntropy`): nats;
  `S = Σ xᵢ ln xᵢ`, `H = ln N − S/N`,
  `H₋ᵢ = ln(N − 1) − (S − xᵢ ln xᵢ + (xᵢ − 1) ln(xᵢ − 1))/(N − 1)` (0 for the last product
  when `xᵢ = 1`), and `N·H − (N − 1)/N · Σ xᵢ H₋ᵢ`, the sums over values above 0 in record
  order. Whole numbers as for the Brillouin index, with `N > 1`. **(implemented)**
- **Grassberger entropy** ([ADR 0559](adr/0559-grassberger-entropy.md);
  `grassberger_entropy(samples)`, C# `Measurements.GrassbergerEntropy`): nats;
  `O(m) = Σ_{j=0}^{m−1} 2/(2j + 1)` over ascending `j`, `A = Σ xᵢ O(⌊xᵢ/2⌋)` over values
  above 0 in record order, and `ln N + γ + ln 2 − A/N`, `γ = 0.5772156649015329`. Whole
  numbers as for the Brillouin index. **(implemented)**
- **Bonachela entropy** ([ADR 0560](adr/0560-bonachela-entropy.md);
  `bonachela_entropy(samples)`, C# `Measurements.BonachelaEntropy`): nats; `h(m)` the
  harmonic numbers over ascending `j` up to `N + 2`, `A = Σ (xᵢ + 1)(h(N + 2) − h(xᵢ + 1))`
  over values above 0 in record order, and `A/(N + 2)`. Whole numbers as for the
  Brillouin index. **(implemented)**
- **Zhang's entropy** ([ADR 0561](adr/0561-zhang-entropy.md);
  `zhang_entropy(samples)`, C# `Measurements.ZhangEntropy`): nats; for a value `x`,
  `P ← P · (1 − (x − 1)/(N − v))`, `T ← T + P/v` for `v = 1, …, N − x` from `P = 1`,
  `T = 0`, and `Σ (xᵢ/N) · T(xᵢ)` over values above 0 in record order. Whole numbers
  totalling more than 1 and at most 10 000. **(implemented)**
- **Chao–Wang–Jost entropy** ([ADR 0562](adr/0562-chao-wang-jost-entropy.md);
  `chao_wang_jost_entropy(samples)`, C# `Measurements.ChaoWangJostEntropy`): nats;
  `Σ (xᵢ/N)(h(N − 1) − h(xᵢ − 1))` over values from 1 to `N − 1` in record order, plus
  `(F₁/N)·B`, `B = q Σ_{m≥0} qᵐ/(N + m)` (until a term leaves the sum unchanged) when
  `A·N ≥ 1` and `q^{1−N}(−ln A − Σ_{r<N} q^r/r)` otherwise, `q = 1 − A`. Whole numbers
  totalling more than 1 and at most 10 000. **(implemented)**
- **Hill number** ([ADR 0563](adr/0563-hill-number.md); `hill_number(samples, order)`,
  C# `Measurements.HillNumber`): `pᵢ = xᵢ/S` over values above 0; the count at `q = 0`,
  `exp(−Σ pᵢ ln pᵢ)` at `q = 1`, `exp(log1p(Σ pᵢ·expm1((q − 1) ln pᵢ))/(1 − q))` when
  `|q − 1| < 1/2`, else `exp((q ln m + ln Σ (pᵢ/m)^q)/(1 − q))`, `m = max pᵢ`; sums in record
  order. Records as for the Gini coefficient; `order` finite, at least 0. **(implemented)**
- **Hill evenness** ([ADR 0564](adr/0564-hill-evenness.md);
  `hill_evenness(samples, order)`, C# `Measurements.HillEvenness`): the Hill number of
  order `q` over `K`, the count of values above 0; from `1/K` to 1, 1 at `q = 0`. Arguments
  as for the Hill number. **(implemented)**
- **Patil–Taillie diversity** ([ADR 0565](adr/0565-patil-taillie-diversity.md);
  `patil_taillie_diversity(samples, beta)`, C# `Measurements.PatilTaillieDiversity`):
  `pᵢ = xᵢ/S` over values above 0; `−Σ pᵢ ln pᵢ` at `β = 0`, else
  `−(Σ pᵢ·expm1(β ln pᵢ))/β`, sums in record order. Records as for the Gini coefficient;
  `beta` finite, at least −1. **(implemented)**
- **Rényi diversity of counts** ([ADR 0566](adr/0566-renyi-diversity.md);
  `renyi_diversity(samples, order)`, C# `Measurements.RenyiDiversity`): nats; the Hill
  number's forms without the outer `exp`: `ln K` at `q = 0`, `−Σ pᵢ ln pᵢ` at `q = 1`,
  `log1p(Σ pᵢ·expm1((q − 1) ln pᵢ))/(1 − q)` when `|q − 1| < 1/2`, else
  `(q ln m + ln Σ (pᵢ/m)^q)/(1 − q)`. Arguments as for the Hill number. **(implemented)**
- **Rényi evenness** ([ADR 0567](adr/0567-renyi-evenness.md);
  `renyi_evenness(samples, order)`, C# `Measurements.RenyiEvenness`): the Rényi diversity
  of counts of order `q` over `ln K`, `K` the count of values above 0; from 0 to 1, 1 at
  `q = 0`. Arguments as for the Hill number, with `K ≥ 2`. **(implemented)**
- **Tsallis diversity of counts** ([ADR 0568](adr/0568-tsallis-diversity.md);
  `tsallis_diversity(samples, order)`, C# `Measurements.TsallisDiversity`):
  `pᵢ = xᵢ/S` over values above 0; `−Σ pᵢ ln pᵢ` at `q = 1`, else
  `−(Σ pᵢ·expm1((q − 1) ln pᵢ))/(q − 1)`, sums in record order. Arguments as for the Hill
  number. **(implemented)**
- **Tsallis evenness** ([ADR 0569](adr/0569-tsallis-evenness.md);
  `tsallis_evenness(samples, order)`, C# `Measurements.TsallisEvenness`): the Tsallis
  diversity of counts of order `q` over its maximum, `ln K` at `q = 1`, else
  `−expm1((1 − q) ln K)/(q − 1)`, `K` the count of values above 0; from 0 to 1, 1 at
  `q = 0`. Arguments as for the Hill number, with `K ≥ 2`. **(implemented)**
- **Sharma–Mittal diversity of counts**
  ([ADR 0570](adr/0570-sharma-mittal-diversity.md); `sharma_mittal_diversity(samples,
  order, degree)`, C# `Measurements.SharmaMittalDiversity`): with `R` the Rényi diversity
  of counts of order `q`, `R` at `r = 1`, else `expm1((1 − r) R)/(1 − r)`. Arguments as for
  the Hill number; `degree` finite. **(implemented)**
- **Pianka's niche overlap** ([ADR 0571](adr/0571-pianka-overlap.md);
  `pianka_overlap(x, y)`, C# `Measurements.PiankaOverlap`): each record over its largest
  value, then `Σ xᵢyᵢ/√(Σ xᵢ² · Σ yᵢ²)`, sums in record order, capped at 1. Records real,
  finite, at least 0, not empty, each with a value above 0, the same length.
  **(implemented)**
- **Proportional similarity** ([ADR 0572](adr/0572-czekanowski-similarity.md);
  `czekanowski_similarity(x, y)`, C# `Measurements.CzekanowskiSimilarity`): each record over
  its largest value, then over its total, sums in record order; `Σ min(pᵢ, qᵢ)` in record
  order, capped at 1. Records as for Pianka's niche overlap. **(implemented)**
- **Morisita–Horn overlap** ([ADR 0573](adr/0573-morisita-horn-overlap.md);
  `morisita_horn_overlap(x, y)`, C# `Measurements.MorisitaHornOverlap`): each record over
  its largest value, then over its total, sums in record order; `2 Σ pᵢqᵢ/(Σ pᵢ² + Σ qᵢ²)`,
  sums in record order, capped at 1. Records as for Pianka's niche overlap.
  **(implemented)**
- **Horn's information overlap** ([ADR 0574](adr/0574-horn-overlap.md);
  `horn_overlap(x, y)`, C# `Measurements.HornOverlap`): both records over the largest value
  in either; each term `a·log1p(b/a) + b·log1p(a/b)`, 0 when `a` or `b` is 0; the sum of
  terms over the same form on the totals, sums in record order, capped at 1. Records as for
  Pianka's niche overlap. **(implemented)**
- **Whittaker's beta of two records** ([ADR 0575](adr/0575-whittaker-beta.md);
  `whittaker_beta(x, y)`, C# `Measurements.WhittakerBeta`): with `a` the kinds above 0 in
  both records and `b`, `c` those above 0 in one only, `(b + c)/(2a + b + c)`. Records as
  for Pianka's niche overlap. **(implemented)**
- **Simpson's beta of two records** ([ADR 0576](adr/0576-simpson-beta.md);
  `simpson_beta(x, y)`, C# `Measurements.SimpsonBeta`): with `a` the kinds above 0 in both
  records and `b`, `c` those above 0 in one only, `min(b, c)/(a + min(b, c))`. Records as
  for Pianka's niche overlap. **(implemented)**
- **Nestedness part of the Sørensen dissimilarity**
  ([ADR 0577](adr/0577-nestedness-beta.md); `nestedness_beta(x, y)`, C#
  `Measurements.NestednessBeta`): with `a` the kinds above 0 in both records and `b`, `c`
  those above 0 in one only, `|b − c|·a/((2a + b + c)(a + min(b, c)))`, one division of
  exact integers. Records as for Pianka's niche overlap. **(implemented)**
- **Turnover part of the Jaccard dissimilarity**
  ([ADR 0578](adr/0578-jaccard-turnover.md); `jaccard_turnover(x, y)`, C#
  `Measurements.JaccardTurnover`): with `a` the kinds above 0 in both records and `b`, `c`
  those above 0 in one only, `2 min(b, c)/(a + 2 min(b, c))`. Records as for Pianka's niche
  overlap. **(implemented)**
- **Nestedness part of the Jaccard dissimilarity**
  ([ADR 0579](adr/0579-jaccard-nestedness.md); `jaccard_nestedness(x, y)`, C#
  `Measurements.JaccardNestedness`): with `a` the kinds above 0 in both records and `b`, `c`
  those above 0 in one only, `|b − c|·a/((a + b + c)(a + 2 min(b, c)))`, one division of
  exact integers. Records as for Pianka's niche overlap. **(implemented)**
- **Ružička similarity of two records**
  ([ADR 0580](adr/0580-ruzicka-similarity.md); `ruzicka_similarity(x, y)`, C#
  `Measurements.RuzickaSimilarity`): `Σ min(x_i, y_i)/Σ max(x_i, y_i)` on the raw values,
  both records first divided by the larger of their maxima, sums in index order. Records as
  for Pianka's niche overlap. **(implemented)**
- **Morisita's overlap of two count records**
  ([ADR 0581](adr/0581-morisita-overlap.md); `morisita_overlap(x, y)`, C#
  `Measurements.MorisitaOverlap`): with totals `X`, `Y` and `S = Σ n(n − 1)` of each record,
  `2 Σ x y (X − 1)(Y − 1)/(S_x Y(Y − 1) + S_y X(X − 1))`. Counts whole, at least 0, each
  record totalling from 2 to 10 000 000, the same length, some count above 1.
  **(implemented)**
- **Balanced-variation part of the Bray–Curtis dissimilarity**
  ([ADR 0582](adr/0582-bray-curtis-balanced.md); `bray_curtis_balanced(x, y)`, C#
  `Measurements.BrayCurtisBalanced`): with both records divided by the larger of their
  maxima, `A = Σ min(x_i, y_i)`, `B = Σ (x_i − min)`, `C = Σ (y_i − min)` in index order,
  `min(B, C)/(A + min(B, C))`. Records as for Pianka's niche overlap. **(implemented)**
- **Abundance-gradient part of the Bray–Curtis dissimilarity**
  ([ADR 0583](adr/0583-bray-curtis-gradient.md); `bray_curtis_gradient(x, y)`, C#
  `Measurements.BrayCurtisGradient`): with `A`, `B`, `C` as for the balanced-variation part,
  `|B − C|·A/((2A + B + C)(A + min(B, C)))`. Records as for Pianka's niche overlap.
  **(implemented)**
- **Podani's replacement part of the Jaccard dissimilarity**
  ([ADR 0584](adr/0584-podani-replacement.md); `podani_replacement(x, y)`, C#
  `Measurements.PodaniReplacement`): with `a` the kinds above 0 in both records and `b`, `c`
  those above 0 in one only, `2 min(b, c)/(a + b + c)`. Records as for Pianka's niche
  overlap. **(implemented)**
- **Podani's richness-difference part of the Jaccard dissimilarity**
  ([ADR 0585](adr/0585-podani-richness-difference.md); `podani_richness_difference(x, y)`,
  C# `Measurements.PodaniRichnessDifference`): with `a` the kinds above 0 in both records
  and `b`, `c` those above 0 in one only, `|b − c|/(a + b + c)`. Records as for Pianka's
  niche overlap. **(implemented)**
- **Replacement part of the Ružička dissimilarity**
  ([ADR 0586](adr/0586-ruzicka-replacement.md); `ruzicka_replacement(x, y)`, C#
  `Measurements.RuzickaReplacement`): with `A = Σ min(xᵢ, yᵢ)`, `B = Σ xᵢ − A` and
  `C = Σ yᵢ − A`, `2 min(B, C)/(A + B + C)`. Records as for Pianka's niche overlap.
  **(implemented)**
- **Richness-difference part of the Ružička dissimilarity**
  ([ADR 0587](adr/0587-ruzicka-richness-difference.md); `ruzicka_richness_difference(x, y)`,
  C# `Measurements.RuzickaRichnessDifference`): with `A`, `B`, `C` as for the replacement
  part, `|B − C|/(A + B + C)`. Records as for Pianka's niche overlap. **(implemented)**
- **Podani's nestedness** ([ADR 0588](adr/0588-podani-nestedness.md);
  `podani_nestedness(x, y)`, C# `Measurements.PodaniNestedness`): with `a` the kinds above 0
  in both records and `b`, `c` those above 0 in one only, 0 when `a = 0`, else
  `(a + |b − c|)/(a + b + c)`. Records as for Pianka's niche overlap. **(implemented)**
- **Harrison's beta** ([ADR 0589](adr/0589-harrison-beta.md); `harrison_beta(x, y)`, C#
  `Measurements.HarrisonBeta`): with `a` the kinds above 0 in both records and `b`, `c` those
  above 0 in one only, `min(b, c)/(a + max(b, c))`, Harrison, Ross and Lawton's `β_H2` for
  two records. Records as for Pianka's niche overlap. **(implemented)**
- **Cody's beta** ([ADR 0590](adr/0590-cody-beta.md); `cody_beta(x, y)`, C#
  `Measurements.CodyBeta`): with `b`, `c` the kinds above 0 in one record only, `(b + c)/2`,
  the mean of the kinds gained and lost; a count, not a ratio. Records as for Pianka's niche
  overlap. **(implemented)**
- **Wilson and Shmida's beta** ([ADR 0591](adr/0591-wilson-shmida-beta.md);
  `wilson_shmida_beta(x, y)`, C# `Measurements.WilsonShmidaBeta`): with `a` the kinds above
  0 in both records and `b`, `c` those above 0 in one only, `(b + c)/(2a + b + c)`, the kinds
  gained and lost over twice the mean richness. Records as for Pianka's niche overlap.
  **(implemented)**
- **Magurran's beta** ([ADR 0592](adr/0592-magurran-beta.md); `magurran_beta(x, y)`, C#
  `Measurements.MagurranBeta`): with `a` the kinds above 0 in both records and `b`, `c` those
  above 0 in one only, `(2a + b + c)(1 − a/(a + b + c))`; a count, not a ratio. Records as
  for Pianka's niche overlap. **(implemented)**
- **Williams' beta** ([ADR 0593](adr/0593-williams-beta.md); `williams_beta(x, y)`, C#
  `Measurements.WilliamsBeta`): with `a` the kinds above 0 in both records and `b`, `c` those
  above 0 in one only, `min(b, c)/(a + b + c)`, from 0 to 1/2. Records as for Pianka's niche
  overlap. **(implemented)**
- **Lennon's gradient beta** ([ADR 0594](adr/0594-lennon-gradient-beta.md);
  `lennon_gradient_beta(x, y)`, C# `Measurements.LennonGradientBeta`): with `a` the kinds
  above 0 in both records and `b`, `c` those above 0 in one only, `2|b − c|/(2a + b + c)`,
  from 0 to below 2. Records as for Pianka's niche overlap. **(implemented)**
- **Routledge's information beta** ([ADR 0595](adr/0595-routledge-information-beta.md);
  `routledge_information_beta(x, y)`, C# `Measurements.RoutledgeInformationBeta`): with `a`
  the kinds above 0 in both records, `b`, `c` those above 0 in one only, `p = a + b`,
  `q = a + c` and `n = p + q`, `ln n − (2a ln 2 + (p ln p + q ln q))/n` (natural logarithm),
  held at 0 from below; from 0 to `ln 2`. Records as for Pianka's niche overlap.
  **(implemented)**
- **Routledge's exponential beta** ([ADR 0596](adr/0596-routledge-exponential-beta.md);
  `routledge_exponential_beta(x, y)`, C# `Measurements.RoutledgeExponentialBeta`):
  `exp(β-I) − 1`, with `β-I` Routledge's information beta, held at 0 from below; from 0 to 1.
  Records as for Pianka's niche overlap. **(implemented)**
- **Routledge's overlap beta** ([ADR 0597](adr/0597-routledge-overlap-beta.md);
  `routledge_overlap_beta(x, y)`, C# `Measurements.RoutledgeOverlapBeta`): with `a` the
  kinds above 0 in both records and `b`, `c` those above 0 in one only,
  `2bc/((a + b + c)² − 2bc)`, from 0 to 1. Records as for Pianka's niche overlap.
  **(implemented)**
- **Schoener's overlap** ([ADR 0598](adr/0598-schoener-overlap.md);
  `schoener_overlap(x, y)`, C# `Measurements.SchoenerOverlap`): `Σ min(p_i, q_i)` on the
  shares `p = x/Σx`, `q = y/Σy`, equal to `1 − ½ Σ|p_i − q_i|`; each record is divided by its
  largest value before it is summed, and the result is held at 1 from above; from 0 to 1.
  Records as for Pianka's niche overlap. **(implemented)**
- **Petraitis' specific overlap** ([ADR 0599](adr/0599-petraitis-overlap.md);
  `petraitis_overlap(x, y)`, C# `Measurements.PetraitisOverlap`): `exp(Σ p_i (ln q_i − ln p_i))`
  over the kinds with `p_i > 0`, on the shares `p = x/Σx`, `q = y/Σy`; 0 when some such kind
  has `q_i = 0`; held at 1 from above; not symmetric. Each record is divided by its largest
  value before it is summed. Records as for Pianka's niche overlap. **(implemented)**
- **Hurlbert's niche overlap** ([ADR 0600](adr/0600-hurlbert-overlap.md);
  `hurlbert_overlap(x, y, available)`, C# `Measurements.HurlbertOverlap`): `Σ p_i q_i/r_i`
  on the shares of use `p = x/Σx`, `q = y/Σy` and of availability `r = available/Σavailable`;
  1 when both use the kinds as they are available, 0 when they share none, no upper bound.
  Each record is divided by its largest value before it is summed. Records as for Pianka's
  niche overlap; `available` above 0 everywhere; an availability share that underflows to 0
  or a sum that overflows is `invalid_argument`. **(implemented)**
- **Hurlbert's niche breadth** ([ADR 0601](adr/0601-hurlbert-niche-breadth.md);
  `hurlbert_niche_breadth(x, available, standardized=False)`, C#
  `Measurements.HurlbertNicheBreadth`): `B' = 1/Σ p_i²/r_i` on the shares of use
  `p = x/Σx` and of availability `r = available/Σavailable`, held at 1 from above; with
  `standardized`, `(B' − r_min)/(1 − r_min)` held to 0 to 1, which needs at least two kinds.
  Each record is divided by its largest value before it is summed. Records as for
  Hurlbert's niche overlap; an availability share that underflows to 0 or a sum that
  overflows is `invalid_argument`. **(implemented)**
- **Manly's alpha** ([ADR 0602](adr/0602-manly-alpha.md); `manly_alpha(x, available)`, C#
  `Measurements.ManlyAlpha`): for each kind `(p_i/r_i)/Σ_j(p_j/r_j)` on the shares of use
  `p = x/Σx` and of availability `r = available/Σavailable`, an array summing to 1, each held
  at 1 from above. Each record is divided by its largest value before it is summed. Records
  as for Hurlbert's niche breadth; an availability share that underflows to 0 or a sum of
  ratios that overflows is `invalid_argument`. **(implemented)**
- **Ivlev's electivity** ([ADR 0603](adr/0603-ivlev-electivity.md);
  `ivlev_electivity(x, available)`, C# `Measurements.IvlevElectivity`): for each kind
  `(p_i − r_i)/(p_i + r_i)` on the shares of use `p = x/Σx` and of availability
  `r = available/Σavailable`, an array held to −1 to 1. Each record is divided by its largest
  value before it is summed. Records as for Manly's alpha; an availability share that
  underflows to 0 is `invalid_argument`. **(implemented)**
- **Jacobs' selectivity index** ([ADR 0604](adr/0604-jacobs-selectivity.md);
  `jacobs_selectivity(x, available)`, C# `Measurements.JacobsSelectivity`): for each kind
  `(p_i − r_i)/(p_i (1 − r_i) + r_i (1 − p_i))` on the shares of use `p = x/Σx` and of
  availability `r = available/Σavailable`, 0 where `p_i = r_i`, an array held to −1 to 1.
  Each record is divided by its largest value before it is summed. Records as for Ivlev's
  electivity; an availability share that underflows to 0 is `invalid_argument`.
  **(implemented)**
- **Vanderploeg and Scavia's relativized electivity**
  ([ADR 0605](adr/0605-vanderploeg-scavia-electivity.md);
  `vanderploeg_scavia_electivity(x, available)`, C#
  `Measurements.VanderploegScaviaElectivity`): for each kind `(α_i − 1/n)/(α_i + 1/n)` with
  `α` Manly's alpha and `n` the number of kinds, an array held to −1 to 1. `α` as
  `manly_alpha` computes it, with its rules. **(implemented)**
- **Savage's selection ratio** ([ADR 0606](adr/0606-savage-selection-ratio.md);
  `savage_selection_ratio(x, available)`, C# `Measurements.SavageSelectionRatio`): for each
  kind `p_i/r_i` on the shares of use `p = x/Σx` and of availability
  `r = available/Σavailable`, an array at least 0, 1 for a kind used as it is available.
  Each record is divided by its largest value before it is summed. Records as for Manly's
  alpha; an availability share that underflows to 0 or a ratio that overflows is
  `invalid_argument`. **(implemented)**
- **Strauss' linear selection index** ([ADR 0607](adr/0607-strauss-selection.md);
  `strauss_selection(x, available)`, C# `Measurements.StraussSelection`): for each kind
  `p_i − r_i` on the shares of use `p = x/Σx` and of availability `r = available/Σavailable`,
  an array from −1 to 1. Each record is divided by its largest value before it is summed.
  Records as for Savage's selection ratio, except that an availability share that underflows
  to 0 is allowed. **(implemented)**
- **Johnson's rank preference index** ([ADR 0608](adr/0608-johnson-rank-preference.md);
  `johnson_rank_preference(x, available)`, C# `Measurements.JohnsonRankPreference`): for each
  kind the rank of its use less the rank of its availability, ranks from 1 for the largest,
  ties given their mean rank, taken on the values as given; negative for a preferred kind;
  the values sum to 0. Records as for Strauss' linear selection index. **(implemented)**
- **Lloyd's mean crowding** ([ADR 0609](adr/0609-lloyd-mean-crowding.md);
  `lloyd_mean_crowding(counts)`, C# `Measurements.LloydMeanCrowding`): `Σ x_i (x_i − 1)/Σ x_i`
  on counts of individuals in sampling units, formed as `t c/s_1` with `t` the
  largest count, `s_1 = Σ x/t` and `c = Σ (x/t)((x − 1)/t)`, `x − 1` formed before scaling
  so counts of 1 add exact zeros; held at 0 from below. Counts are whole numbers at least 0 with a total above
  0. **(implemented)**
- **Lloyd's index of patchiness** ([ADR 0610](adr/0610-lloyd-patchiness.md);
  `lloyd_patchiness(counts)`, C# `Measurements.LloydPatchiness`): the mean crowding over the
  mean count per unit, `m*/m`, formed as `(c/s_1) · n/s_1` with `t`, `s_1` and `c` as for
  Lloyd's mean crowding, held at 0 from below. Counts as for Lloyd's mean
  crowding. **(implemented)**
- **Green's index of dispersion** ([ADR 0611](adr/0611-green-index.md);
  `green_index(counts)`, C# `Measurements.GreenIndex`): `(s²/m − 1)/(Σx − 1)` with `m` the
  mean count and `s²` the sample variance (divided by `n − 1`), formed as
  `((w n/s_1)/(n − 1) − 1/t)/(s_1 − 1/t)` with `t` the largest count,
  `s_1 = Σ x/t` and `w = Σ((x − m̂)/t)²` about `m̂ = t (s_1/n)`, a second pass so a mean
  large next to the spread does not cancel; held to [−1, 1]. Counts as for Lloyd's mean crowding,
  with at least two units and a total above 1. **(implemented)**
- **Morisita's index of dispersion** ([ADR 0612](adr/0612-morisita-dispersion.md);
  `morisita_dispersion(counts)`, C# `Measurements.MorisitaDispersion`):
  `n Σ x_i (x_i − 1)/(Σx (Σx − 1))` on counts in `n` units, formed as
  `n c/(s_1 (s_1 − 1/t))` with `t`, `s_1` and `c` as for Lloyd's mean
  crowding, held to [0, n]. Counts as for Green's index of dispersion.
  **(implemented)**
- **David and Moore's index of clumping** ([ADR 0613](adr/0613-david-moore-clumping.md);
  `david_moore_clumping(counts)`, C# `Measurements.DavidMooreClumping`): `s²/m − 1` with `m`
  the mean count and `s²` the sample variance (divided by `n − 1`), formed as
  `t (w n/s_1)/(n − 1) − 1` with `t`, `s_1` and `w` as for Green's index, held at
  −1 from below. Counts as for Lloyd's mean crowding, with at least
  two units. **(implemented)**
- **Cassie's index** ([ADR 0614](adr/0614-cassie-index.md); `cassie_index(counts)`, C#
  `Measurements.CassieIndex`): `(s² − m)/m²` with `m` the mean count and `s²` the sample
  variance (divided by `n − 1`), formed as `(A − 1/t) · n/s_1` with `t` the largest count,
  `s_1` and `w` as for Green's index and
  `A = (w n/s_1)/(n − 1)`. Counts as for David
  and Moore's index of clumping. **(implemented)**
- **Fisher's index of dispersion statistic** ([ADR 0615](adr/0615-fisher-dispersion.md);
  `fisher_dispersion(counts)`, C# `Measurements.FisherDispersion`): `Σ(x_i − m)²/m` with `m`
  the mean count, formed as `t (w n/s_1)` with `t`, `s_1` and `w` as for Green's index; a value that overflows is refused. Counts as
  for David and Moore's index of clumping. **(implemented)**
- **The Clark–Evans aggregation index** ([ADR 0616](adr/0616-clark-evans-ratio.md);
  `clark_evans_ratio(distances, density)`, C# `Measurements.ClarkEvansRatio`): the mean
  nearest-neighbour distance over `1/(2√ρ)`, its mean for individuals placed at random with
  `ρ` individuals per unit area: `2 r̄ √ρ`, formed as `(t (s_1/n)) (2√ρ)` with `t` the
  largest distance and `s_1 = Σ d/t`; 0 when every distance is 0; a value that overflows is
  refused. Distances finite, at least 0, not empty; density finite and above 0.
  **(implemented)**
- **The Clark–Evans test statistic** ([ADR 0617](adr/0617-clark-evans-z.md);
  `clark_evans_z(distances, density)`, C# `Measurements.ClarkEvansZ`): `(r̄ − r_E)/σ` with
  `r_E = 1/(2√ρ)` and the exact standard error `σ = √((4 − π)/(4πρn))` (Clark and Evans
  rounded it to `0.26136/√(nρ)`), formed as `(R − 1) √(nπ/(4 − π))` with `R` the
  Clark–Evans aggregation index; a value that overflows is refused. Arguments as for the
  aggregation index. **(implemented)**
- **Hopkins' statistic** ([ADR 0618](adr/0618-hopkins-statistic.md);
  `hopkins_statistic(point_distances, individual_distances)`, C#
  `Measurements.HopkinsStatistic`): `Σu²/(Σu² + Σw²)`, `u` the distances from random points
  to the nearest individual and `w` from individuals to their nearest neighbour. Formed as
  `a/(a + b)` with `t` the largest distance in either sample, `a = Σ(u/t)²`,
  `b = Σ(w/t)²`; held to [0, 1]. Each sample finite, at least 0, not empty, with a value
  above 0; the two need not be the same size. **(implemented)**
- **Pielou's index of non-randomness** ([ADR 0619](adr/0619-pielou-nonrandomness.md);
  `pielou_nonrandomness(point_distances, density)`, C# `Measurements.PielouNonrandomness`):
  `πρ Σu²/n`, `u` the distances from random points to the nearest individual and `ρ` the
  individuals per unit area. Formed as `p²` with `t` the largest distance,
  `a = Σ(u/t)²` and `p = (t √(a/n)) (√π √ρ)`, so nothing overflows or rounds in the
  subnormal range unless the value does; 0 when every distance is 0; a value that overflows
  is refused. Distances finite, at least 0, not empty; density finite and above 0.
  **(implemented)**
- **Eberhardt's index** ([ADR 0620](adr/0620-eberhardt-index.md);
  `eberhardt_index(point_distances)`, C# `Measurements.EberhardtIndex`): `n Σu²/(Σu)²`, `u`
  the distances from random points to the nearest individual. Formed as `n s_2/(s_1 s_1)`
  with `t` the largest distance, `s_1 = Σ u/t` and `s_2 = Σ(u/t)²`; held to [1, n]. This is
  `σ²/ū² + 1` with `σ²` over `n`; Krebs' `(s/ū)² + 1` uses `s²` over `n − 1`, which is
  `1 + (I − 1) n/(n − 1)`. Distances finite, at least 0, with a value above 0. **(implemented)**
- **Sample entropy** ([ADR 0326](adr/0326-sample-entropy.md); `sample_entropy(samples, m, r)`,
  C# `Measurements.SampleEntropy`): `L = N − m` template starts for both lengths `m` and `m+1`;
  a pair `i < l` matches when `max_j |x[i+j] − x[l+j]| ≤ r`; `B`, `A` the matching pairs at
  `m` and `m+1`; `−ln(A/B)`, `+∞` when `A = 0`. `r` in sample units, not scaled by σ. Real,
  finite, `N ≥ m + 2`; integer `m ≥ 1`; finite `r ≥ 0`; `B > 0`. **(implemented)**
- **Permutation entropy** ([ADR 0325](adr/0325-permutation-entropy.md);
  `permutation_entropy(samples, order, delay=1)`, C# `Measurements.PermutationEntropy`): windows
  `v_j = x[i + j·delay]`, `j < order`, `i < L = N − (order−1)·delay`; each window's pattern is
  its stable ascending sort order (ties by index); `H = −Σ p ln p / ln(order!)` over the
  patterns' shares. Real, finite samples; integer `2 ≤ order ≤ 8`, integer `delay ≥ 1`,
  `L ≥ 1`. **(implemented)**
- **Hjorth parameters** ([ADR 0324](adr/0324-hjorth-parameters.md);
  `hjorth_parameters(samples)`, C# `Measurements.HjorthParameters`): `var` the population
  variance; `d[n] = x[n+1] − x[n]`, `dd[n] = d[n+1] − d[n]`; `activity = var(x)`,
  `mobility = sqrt(var(d)/var(x))`, `complexity = sqrt(var(dd)/var(d)) / mobility`; per sample,
  not per second. Gives `HjorthParameters(activity, mobility, complexity)`. Real, finite, at
  least 3 samples, `var(x) > 0` and `var(d) > 0`. **(implemented)**
- **Temporal centroid** ([ADR 0147](adr/0147-temporal-centroid.md);
  `temporal_centroid(samples, sample_rate)`, C# `Measurements.TemporalCentroid`): weights
  `p_n = |x[n]|²` at `t_n = n / fs` (sample 0 at t = 0); `centroid = Σ p t / Σ p` and
  `spread = sqrt(Σ p (t − centroid)² / Σ p)`, both in seconds. Gives `TemporalCentroid(centroid,
  spread)`. Real or complex, finite, at least one sample, energy above 0; `sample_rate` finite
  and positive. **(implemented)**
- **GCC-PHAT delay** ([ADR 0191](adr/0191-gcc-phat.md); `gcc_phat(x, y, sample_rate, *,
  max_delay=None)`, C# `Measurements.GccPhat`): pad both to `L = N + M − 1`; `G = X·conj Y`,
  `W = G/|G|` (0 where `|G| = 0`), `r = Re ifft(W)`; circular index `i` is lag `i` for `i < N`,
  else `i − L` (the `cross_correlation` sign). Search lags `−(M−1) … N−1`, with `|k| ≤
  ⌊max_delay·fs⌋` when given; `lag` the largest `r`, smallest lag on ties; parabolic `δ` when
  both neighbours are searched and the curvature is negative, else 0. Result `GccPhat(delay =
  (lag + δ)/fs, lag, peak = r[lag])`. Real, 1-D, finite, not empty, not all zero;
  `sample_rate` finite and positive; `max_delay` finite, `≥ 0`. **(implemented)**
- **Energy separation** ([ADR 0189](adr/0189-energy-separation.md); `energy_separation(samples,
  sample_rate)`, C# `Measurements.EnergySeparation`): DESA-2 with `y[n] = x[n+1] − x[n−1]`; where
  `ψ[x] > 0` and `ψ[y] > 0`, `c = 1 − ψ[y]/(2ψ[x])` clamped to `[−1, 1]`, frequency
  `½·arccos(c)·fs/(2π)` in `[0, fs/4]`, amplitude `2ψ[x]/√ψ[y]`; elsewhere both NaN. Result
  `EnergySeparation(amplitude, frequency)`, `N − 4` values for `n = 2 … N−3`. Real, 1-D,
  finite, at least five samples; `sample_rate` finite and positive. **(implemented)**
- **Teager-Kaiser energy** ([ADR 0188](adr/0188-teager-energy.md); `teager_energy(samples)`, C#
  `Measurements.TeagerEnergy`): `ψ[n] = |x[n]|² − Re(x[n−1]·conj x[n+1])`, `n = 1 … N−2`, so
  `N − 2` values with no padding; real input gives `x[n]² − x[n−1]x[n+1]`. Real or complex,
  1-D, finite, at least three samples. **(implemented)**
- **Energy-time curve** ([ADR 0186](adr/0186-energy-time-curve.md); `energy_time_curve(
  impulse_response)`, C# `Measurements.EnergyTimeCurve`): `10·log10(|z[n]|²/max|z|²)` dB with `z`
  the `analytic_signal` (ADR 0185); peak 0 dB, zero gives `−inf`, no smoothing. Real, 1-D,
  finite, not empty, not all zero. **(implemented)**
- **Decay time from a curve** ([ADR 0184](adr/0184-decay-time.md); `decay_time(decay,
  sample_rate, *, start_db=-5, stop_db=-25)`, C# `Measurements.DecayTime`): the ADR 0171 fit on
  a supplied real dB curve; `reverberation_time(h, …)` is `decay_time(schroeder_decay(h), …)`.
  The curve may hold `−inf` (below every level), not NaN or `+inf`; one-dimensional, not empty;
  the same threshold samples and errors. **(implemented)**
- **Noise-compensated decay** ([ADR 0183](adr/0183-noise-compensated-decay.md);
  `noise_compensated_decay(impulse_response, *, tail=0.1)`, C# `Measurements.NoiseCompensatedDecay`):
  noise window the last `M = ⌊tail·N + 1/2⌋` samples (`1 ≤ M < N`), `ν` their mean `|h|²`;
  `E[n] = Σ_{k=n}^{N−M−1} (|h[k]|² − ν)` for `n < N − M`; result `10 log10(E[n]/E[0])`, `N − M`
  values, `−inf` where `E[n] ≤ 0`; `E[0] ≤ 0` invalid. `tail` finite in `(0, 1)`; real or
  complex, finite, not empty. **(implemented)**
- **Decay curvature** ([ADR 0182](adr/0182-decay-curvature.md); `decay_curvature(impulse_response,
  sample_rate)`, C# `Measurements.DecayCurvature`): `C = 100·(T30/T20 − 1)` percent with T20
  the `reverberation_time` fit from −5 to −25 dB and T30 from −5 to −35 dB; signed, unclipped;
  the same rules and errors (the decay must reach −35 dB). **(implemented)**
- **Early decay time** ([ADR 0181](adr/0181-early-decay-time.md); `early_decay_time(impulse_response,
  sample_rate)`, C# `Measurements.EarlyDecayTime`): exactly `reverberation_time` with
  `start_db = 0`, `stop_db = −10`, so the fit starts at sample 0; same rules and errors.
  **(implemented)**
- **Bass and treble ratio** ([ADR 0180](adr/0180-bass-treble-ratio.md); `bass_ratio(times)`,
  `treble_ratio(times)`, C# `Measurements.BassRatio`, `Measurements.TrebleRatio`): `times` is
  exactly six octave-band reverberation times at 125, 250, 500, 1000, 2000, 4000 Hz, all finite
  and positive; `BR = (T125 + T250)/(T500 + T1000)`, `TR = (T2000 + T4000)/(T500 + T1000)`, a
  plain ratio. **(implemented)**
- **Stage support** ([ADR 0179](adr/0179-stage-support.md); `stage_support(impulse_response,
  sample_rate, *, late=False)`, C# `Measurements.StageSupport`): `N(t) = ⌊t·fs + 1/2⌋`; direct
  `[0, N(0.01))`, early `[N(0.02), N(0.1))`, late `[N(0.1), N(1))`, half-open, clipped to the
  length; `10 log10(E_window/E_direct)`. A silent window gives `−inf`; a silent direct window
  or `N(0.01) < 1` is invalid. Real or complex, finite, not empty; `fs` finite and positive.
  **(implemented)**
- **Sound strength** ([ADR 0178](adr/0178-sound-strength.md); `sound_strength(impulse_response,
  reference)`, C# `Measurements.SoundStrength`): `G = 10 log10(Σ|h|² / Σ|h_ref|²)` with the
  reference the free-field response at 10 m; lengths may differ, no sample rate (same rate is
  the caller's), G80 and G_late are the caller's slices. A silent response gives `−inf`; a
  silent reference is invalid. Both real or both complex, one-dimensional, finite, not empty.
  **(implemented)**
- **Speech transmission index** ([ADR 0177](adr/0177-speech-transmission-index.md);
  `speech_transmission_index(mtf)`, C# `Measurements.SpeechTransmissionIndex`): `mtf` is 7 rows
  (octave bands 125 Hz to 8 kHz) by `M ≥ 1` columns. `SNR = 10 log10(m/(1 − m))` clipped to
  ±15 dB (`m ≤ 0`: TI 0; `m ≥ 1`: TI 1), `TI = (SNR + 15)/30`, `MTI_k` the row mean, `STI = Σ
  α_k MTI_k − Σ β_k √(MTI_k MTI_{k+1})` with the IEC 60268-16:2020 male weights `α = 0.085,
  0.127, 0.230, 0.233, 0.309, 0.224, 0.173`, `β = 0.085, 0.078, 0.065, 0.011, 0.047, 0.095`. No
  level, masking or threshold corrections. Values finite. **(implemented)**
- **Modulation transfer function** ([ADR 0176](adr/0176-modulation-transfer.md);
  `modulation_transfer(impulse_response, sample_rate, frequencies)`, C#
  `Measurements.ModulationTransfer`): `m(F) = |Σ |h[n]|² e^{−j2πF n/fs}| / Σ |h[n]|²` from
  index 0, the phase `2π·F·n/fs` in double without reduction; one value per frequency, in order.
  Frequencies finite and `≥ 0` (above `fs/2` allowed), non-empty; response real or complex,
  finite, not empty, not all zero; `fs` finite and positive. **(implemented)**
- **Lateral energy fraction** ([ADR 0175](adr/0175-lateral-fraction.md); `lateral_fraction(omni,
  figure_eight, sample_rate, *, start=0.005, stop=0.08)`, C# `Measurements.LateralFraction`):
  `N_a = ⌊start·fs + 1/2⌋`, `N_b = ⌊stop·fs + 1/2⌋`; `Σ_{N_a ≤ n < N_b} h_8² / Σ_{n < N_b} h_o²`,
  clipped to the length, both from index 0, not clamped (can exceed 1). Real, finite, equal
  non-zero length; `fs` finite and positive; `0 ≤ start < stop` finite, `N_b ≥ 1`; omni energy
  below `N_b` not zero. **(implemented)**
- **Interaural cross-correlation** ([ADR 0174](adr/0174-iacc.md); `iacc(left, right, sample_rate, *,
  max_lag=0.001)`, C# `Measurements.Iacc`): `max_{|τ| ≤ L} |Σ_n l[n] r[n+τ]| / √(Σl² Σr²)` over
  integer lags, `L = ⌊max_lag·fs + 1/2⌋` (lags past the length skipped; `τ > 0`: right lags),
  whole responses, value only. Real, finite, equal non-zero length, neither all zero; `fs`
  finite and positive; `max_lag` finite and `≥ 0`. **(implemented)**
- **Centre time** ([ADR 0173](adr/0173-centre-time.md); `centre_time(impulse_response, sample_rate)`,
  C# `Measurements.CentreTime`): `T_s = Σ (n/fs)|h[n]|² / Σ |h[n]|²` from index 0, in seconds
  (energy-weighted, unlike the envelope-weighted temporal centroid). The early decay time is
  `reverberation_time(h, fs, start_db=0, stop_db=-10)`: the fit starts at `n = 0`. Real or
  complex, finite, not empty, not all zero; `fs` finite and positive. **(implemented)**
- **Clarity and definition** ([ADR 0172](adr/0172-clarity-definition.md); `clarity(impulse_response,
  sample_rate, *, time=0.08)`, `definition(impulse_response, sample_rate, *, time=0.05)`, C#
  `Measurements.Clarity`, `Measurements.Definition`): the response starts at index 0; `N =
  ⌊time·fs + 1/2⌋ ≥ 1`; `E_early = Σ_{n<N}|h|²`, `E_late = Σ_{n≥N}|h|²` (`N` past the end: all
  early). Clarity `10 log10(E_early/E_late)` (`+inf` for no late energy, `−inf` for no early);
  definition `E_early/(E_early + E_late)`. Real or complex, finite, not empty, not all zero;
  `fs` and `time` finite and positive. **(implemented)**
- **Reverberation time** ([ADR 0171](adr/0171-reverberation-time.md); `schroeder_decay(impulse_response)`,
  `reverberation_time(impulse_response, sample_rate, *, start_db=-5.0, stop_db=-25.0)`, C#
  `Measurements.SchroederDecay`, `Measurements.ReverberationTime`): `d[n] = 10 log10(E[n]/E[0])`,
  `E[n] = Σ_{k≥n}|h[k]|²` (zero tail gives `−inf`; no truncation or noise correction). The fit
  is ordinary least squares of `d[n]` on `t = n/fs` over `n1 ≤ n < n2`, `n1`/`n2` the first
  indices with `d ≤ start_db`/`d ≤ stop_db`, at least two samples, slope `m < 0`; `T = −60/m`.
  Real or complex, finite, not empty, not all zero; `fs` finite and positive; `stop_db <
  start_db ≤ 0` finite; never reaching `stop_db` is `invalid_argument`. **(implemented)**
- **Short Leq series and sound exposure** ([ADR 0170](adr/0170-block-leq-and-exposure.md);
  `block_leq(samples, sample_rate, duration)`, `sound_exposure(samples, sample_rate)`, C#
  `Measurements.BlockLeq`, `Measurements.SoundExposure`): `block_leq` is the mean `|x|²` over
  each of the `⌊len/N⌋` consecutive blocks of `N = ⌊duration·fs + 1/2⌋ ≥ 1` samples, a partial
  last block dropped (shorter than `N` gives empty); `sound_exposure` is `Σ|x|²/fs` (empty gives
  0). Real or complex, finite; `sample_rate` and `duration` finite and positive.
  **(implemented)**
- **Exceedance levels** ([ADR 0169](adr/0169-exceedance-levels.md); `exceedance_levels(powers,
  percents)`, C# `Measurements.ExceedanceLevels`): `L_N` is the `q = 1 − N/100` quantile of the
  powers by linear interpolation (Hyndman–Fan type 7): sort ascending, `h = (n − 1)q`, `s_⌊h⌋ +
  (h − ⌊h⌋)(s_⌊h⌋+1 − s_⌊h⌋)`; `L_0` the maximum, `L_100` the minimum; in power, the caller takes
  dB. `powers` not empty, finite, `≥ 0`; `percents` finite in `[0, 100]`, may be empty.
  **(implemented)**
- **Octave-band levels** ([ADR 0168](adr/0168-octave-band-levels.md);
  `octave_band_levels(samples, sample_rate, fraction, min_frequency, max_frequency, *,
  order=3)`, C# `Measurements.OctaveBandLevels`): one mean power per band of `octave_bands(...)`,
  in order: `butterworth_bandpass(order, lower, upper, fs)` from rest (`IirFilter`) over the
  whole input, then the mean of `|y|²`, transient included. Real or complex, finite, not
  empty; every selected upper edge `< fs/2` (else `invalid_argument`); `order ≥ 1`; no band
  gives an empty result. **(implemented)**
- **Time weighting** ([ADR 0166](adr/0166-time-weighting.md);
  `time_weighting(samples, sample_rate, time_constant)`, C# `Measurements.TimeWeighting`):
  `y[n] = α y[n−1] + (1 − α)|x[n]|²`, `y[−1] = 0`, `α = exp(−1/(τ fs))`, `1 − α =
  −expm1(−1/(τ fs))`; one power value per sample (Fast `τ = 0.125` s, Slow `1` s; dB is the
  caller's `lin_to_db`). Real or complex, finite; empty gives empty; `sample_rate` and
  `time_constant` finite and positive. `L_eq` is `power_stats(...).mean_power`.
  **(implemented)**
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
- **ERB scale** (`hz_to_erb_rate(hz)`, `erb_rate_to_hz(erb)`, `erb_bandwidth(hz)`, C#
  `Units.HzToErbRate`, `Units.ErbRateToHz`, `Units.ErbBandwidth`,
  [ADR 0160](adr/0160-erb-scale.md)): Glasberg & Moore (1990) with the published constants:
  `ERB(f) = 24.7·(4.37 f/1000 + 1)` Hz, `E = 21.4·log10(4.37 f/1000 + 1)`, inverse
  `(10^(E/21.4) − 1)·1000/4.37`. Values finite and `≥ 0`. **(implemented)**
- **ERB-spaced frequencies** (`erb_space(min_frequency, max_frequency, n_frequencies)`, C#
  `Units.ErbSpace`, [ADR 0162](adr/0162-erb-space.md)): `f_i = erb_rate_to_hz(E_lo + (E_hi −
  E_lo)·i/(n − 1))`, ascending, first exactly `min` and last exactly `max`; `n = 1` gives
  `[min]`. `0 ≤ min < max` finite, `n ≥ 1`. **(implemented)**
- **Bark scale** (`hz_to_bark(hz)`, `bark_to_hz(bark)`, C# `Units.HzToBark`, `Units.BarkToHz`,
  [ADR 0163](adr/0163-bark-scale.md)): Traunmüller (1990), `z = 26.81 f/(1960 + f) − 0.53`, then
  `z < 2`: `z + 0.15 (2 − z)`; `z > 20.1`: `z + 0.22 (z − 20.1)`. Inverse: below 2 `z = (b −
  0.3)/0.85`, above 20.1 `z = (b + 4.422)/1.22`, then `f = 1960 (z + 0.53)/(26.28 − z)`, clamped
  at 0. `hz` finite and `≥ 0`; `bark` finite, `≥ −0.53 + 0.15 (2 + 0.53)` (computed in floating
  point) and with `z < 26.28`. **(implemented)**
- **Frequency weightings** (`a_weighting(frequency)`, `c_weighting(frequency)`, C#
  `Units.AWeighting`, `Units.CWeighting`, [ADR 0164](adr/0164-frequency-weightings.md)): IEC
  61672-1 curves in dB from the poles `f1 = 20.598997`, `f2 = 107.65265`, `f3 = 737.86223`,
  `f4 = 12194.217` Hz: `A_raw = 20 log10(f4² f⁴/((f² + f1²) √((f² + f2²)(f² + f3²)) (f² +
  f4²)))`, `C_raw = 20 log10(f4² f²/((f² + f1²)(f² + f4²)))`, each minus its own value at
  1000 Hz (so exactly 0 there). `f = 0` gives `−inf`. Finite and `≥ 0`. **(implemented)**
- **Fractional-octave bands** (`octave_bands(fraction, min_frequency, max_frequency)`, C#
  `Units.OctaveBands`, [ADR 0167](adr/0167-octave-bands.md)): IEC 61260-1 base 10, `G =
  10^(3/10)`, `b = fraction`: mid-band `f_m = 1000·G^(x/b)` (odd `b`) or `1000·G^((2x +
  1)/(2b))` (even `b`), edges `f_m·G^(∓1/(2b))`; rows `[lower, center, upper]` ascending for
  every integer `x` with `min ≤ f_m ≤ max` in floating point; none gives 0 rows. `fraction ≥ 1`
  an integer, `0 < min ≤ max` finite. **(implemented)**

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
- **Coherence** ([ADR 0192](adr/0192-coherence.md); `coherence(x, y, sample_rate, *,
  nperseg=None, noverlap=None, window="hann", beta=None, detrend="none", nfft=None)`, C#
  `Spectral.Coherence`): the `welch_psd` segments of `x` and `y` alike; with `X_s`, `Y_s` the
  length-`M` transforms of windowed segment `s`, for bins `k = 0 … ⌊M/2⌋` at `k·fs/M`:
  `Sxy = Σ X_s·conj Y_s`, `Sxx = Σ|X_s|²`, `Syy = Σ|Y_s|²`, `C = min(1, |Sxy|²/(Sxx·Syy))`, NaN
  where `Sxx·Syy = 0` (scale and doubling cancel). Result `Coherence(frequencies, values,
  num_segments)`. Real, 1-D, finite, the same length. **(implemented)**
- **Transfer function (H1)** ([ADR 0193](adr/0193-transfer-function.md);
  `transfer_function(x, y, sample_rate, *, nperseg=None, noverlap=None, window="hann",
  beta=None, detrend="none", nfft=None)`, C# `Spectral.TransferFunction`): the `coherence`
  segments; `H[k] = Σ conj X_s·Y_s / Σ|X_s|²` for `k = 0 … ⌊M/2⌋` at `k·fs/M`, complex NaN where
  `Σ|X_s|² = 0`. Result `TransferFunction(frequencies, response, num_segments)`. The `coherence`
  rules. **(implemented)**
- **Sliding DFT** ([ADR 0231](adr/0231-sliding-dft.md); `sliding_dft(samples, length, k)`, C#
  `Spectral.SlidingDft`): `S_n = Σ_{m=0}^{N−1} x[n − N + 1 + m] e^(−2πi k m/N)`, `N = length`,
  `n = 0 … L−1`, `x` zero before 0 (equal to `fft(x[n−N+1 … n])[k]` once the window is full);
  `S_n = ((S_{n−1} + x[n]) − x[n−N])·w`, `S_{−1} = 0`, `w = cos θ + i sin θ`, `θ = 2πk/N`.
  Finite, non-empty samples; integer `length ≥ 1`; integer `k` in `0 … length − 1`.
  **(implemented)**
- **Goertzel** ([ADR 0224](adr/0224-goertzel.md); `goertzel(samples, sample_rate, frequencies)`,
  C# `Spectral.Goertzel`): unscaled DTFT `X(f) = Σ x[n] e^(−2πi f n/fs)`, `n` from 0 (equal to FFT
  bin `k` at `f = k fs/N`); `s[n] = x[n] + 2cos ω s[n−1] − s[n−2]`,
  `X = e^(−iω(N−1))(s[N−1] − e^(−iω) s[N−2])`. Any finite frequency. Finite, non-empty samples
  and frequencies; sample rate positive and finite. **(implemented)**
- **AR model PSD** ([ADR 0223](adr/0223-ar-psd.md); `ar_psd(coefficients, error, sample_rate,
  nfft, *, one_sided=None)`, C# `Spectral.ArPsd`): two-sided `σ²/(fs·|A_k|²)`,
  `A_k = Σ a_j e^(−2πi jk/M)`, `M = nfft`, folded as Welch. `nperseg = M`, `num_segments = 1`,
  `bin_width = enbw_hz = fs/M`. Filter finite with `a[0] = 1`; error and sample rate positive and
  finite; `nfft ≥ order + 1`; `A_k ≠ 0` on every bin; one-sided needs real coefficients.
  **(implemented)**
- **Burg AR PSD** ([ADR 0204](adr/0204-burg-psd.md); `burg_psd(samples, sample_rate, order, *,
  nfft=None, one_sided=None)`, C# `Spectral.BurgPsd`): `f = b = x`, `σ² = mean |x|²`; per order
  `k = −2 Σ F·B*/Σ(|F|² + |B|²)` with `F = f[1:]`, `B = b[:-1]`, `f ← F + k·B`, `b ← B + k*·F`,
  Levinson's step on `a`, `σ² ← σ²(1 − |k|²)`. Density and fields as Yule-Walker. `|k| ≥ 1` or a
  zero error energy is `invalid_argument`. **(implemented)**
- **Yule-Walker AR PSD** ([ADR 0203](adr/0203-yule-walker-psd.md); `yule_walker_psd(samples,
  sample_rate, order, *, nfft=None, one_sided=None)`, C# `Spectral.YuleWalkerPsd`): biased
  autocorrelation (no mean removal) to lag `p`, Levinson-Durbin for `a` and `σ²`, two-sided
  `σ²/(fs·|A_k|²)` with `A_k = Σ a_j e^(−2πi jk/M)`, folded as Welch (one-sided interior doubled,
  else shifted). `nperseg = N`, `num_segments = 1`, `bin_width = fs/M`, `enbw_hz = fs/N`.
  `1 ≤ order < N`, `nfft ≥ order + 1` (default `N`). **(implemented)**
- **Coherence confidence interval** ([ADR 0202](adr/0202-coherence-confidence-interval.md);
  `coherence_confidence_interval(coherence, num_segments, confidence=0.95)`, C#
  `Spectral.CoherenceConfidenceInterval`): Fisher transform of `γ = √γ²`, `s = z/√(2K − 2)`
  with `z = √q₁(c)` the two-sided normal quantile; `lower = max(0, tanh(atanh γ − s))²`,
  `upper = tanh(atanh γ + s)²`, `γ² = 1` gives `[1, 1]`. Coherence in [0, 1], `K ≥ 2`,
  `0 < c < 1`. Approximate for small `K`. **(implemented)**
- **PSD confidence interval** ([ADR 0201](adr/0201-psd-confidence-interval.md);
  `psd_confidence_interval(psd, dof, confidence=0.95)`, C# `Spectral.PsdConfidenceInterval`):
  `lower = ν·P/q_ν((1+c)/2)`, `upper = ν·P/q_ν((1−c)/2)`, `q_ν` the chi-squared quantile (private;
  regularized incomplete gamma by series or Lentz continued fraction, inverted by safeguarded
  Newton; C# log-gamma by Stirling's series after shifting to ≥ 15). `psd` finite and
  non-negative, `dof > 0`, `0 < c < 1`. Result `(lower, upper)`. **(implemented)**
- **Welch degrees of freedom** ([ADR 0200](adr/0200-welch-dof.md); `welch_dof(nperseg,
  noverlap, num_segments, *, window="hann", beta=None)`, C# `Spectral.WelchDof`):
  `ν = 2K / (1 + 2 Σ_{l=1}^{K−1} (1 − l/K)·ρ(l)²)`, `ρ(l) = Σ w[n]·w[n+l·S] / Σ w²` with step
  `S = nperseg − noverlap` (0 once `l·S ≥ nperseg`), the `welch_psd` window. `K ≥ 1`;
  `K = 1` gives 2. **(implemented)**
- **Coherence threshold** ([ADR 0199](adr/0199-coherence-threshold.md);
  `coherence_threshold(num_segments, alpha=0.05)`, C# `Spectral.CoherenceThreshold`):
  `1 − alpha^(1/(K−1))`, the level independent Gaussian signals exceed with probability `alpha`
  for `K` independent segments; `K ≥ 2` an integer, `0 < alpha < 1`. Overlap is not corrected
  for. **(implemented)**
- **Coherent output power** ([ADR 0198](adr/0198-coherent-output-power.md);
  `coherent_output_power(...)`, the `coherence` arguments, C# `Spectral.CoherentOutputPower`):
  `Pyy` as `welch_psd(y)` on the same bins; `coherent = γ²·Pyy`, `noncoherent = Pyy − coherent`,
  with `γ²` taken as 0 where `Sxx·Syy = 0` (no NaN). Result `(frequencies, coherent,
  noncoherent, num_segments)`. **(implemented)**
- **Complex coherence and transfer functions** ([ADR
  0197](adr/0197-complex-coherence-transfer.md)): complex `x` or `y` in `coherence`,
  `transfer_function` or `transfer_function_h2` uses all `M` bins in `fftshift` order with
  `fft_frequencies(M, fs, shifted=True)`; the definitions and NaN rules are unchanged; real input
  stays one-sided, and there is no `one_sided` argument. C# `Complex` overloads. **(implemented)**
- **Transfer function (H2)** ([ADR 0195](adr/0195-transfer-function-h2.md);
  `transfer_function_h2(...)`, the `transfer_function` arguments, C#
  `Spectral.TransferFunctionH2`): `H2[k] = Σ|Y_s|² / Σ conj Y_s·X_s` on the same bins, complex NaN
  where the denominator is 0; the `TransferFunction` result. `H1/H2` is the coherence.
  **(implemented)**
- **Cross-spectral density** ([ADR 0194](adr/0194-cross-spectral-density.md);
  `cross_spectral_density(x, y, sample_rate, *, nperseg=None, noverlap=None, window="hann",
  beta=None, detrend="none", nfft=None)`, C# `Spectral.CrossSpectralDensity`): the `coherence`
  segments; `Pxy[k] = d_k·Σ conj X_s·Y_s / (K·fs·Σw²)` for `k = 0 … ⌊M/2⌋` at `k·fs/M`, with the
  `welch_psd` doubling `d_k`; `y = x` gives `welch_psd`. Result `CrossSpectralDensity(frequencies,
  csd, num_segments)`. `one_sided` as for `welch_psd` ([ADR
  0196](adr/0196-complex-cross-spectral-density.md)): complex `x` or `y` (or `one_sided=False`)
  gives the two-sided `Σ conj X_s·Y_s / (K·fs·Σw²)` over all `M` bins, undoubled, in `fftshift`
  order with `fft_frequencies(M, fs, shifted=True)`; C# a `Complex` overload, and `oneSided` on the
  real one. 1-D, finite, the same length. **(implemented)**
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
- **Analytic signal** (`analytic_signal(samples)`, C# `Spectral.AnalyticSignal`,
  [ADR 0185](adr/0185-analytic-signal.md)): `z = ifft(fft(x)·W)` with `W[0] = 1`, `W[k] = 2`
  for `0 < 2k < N`, `W[N/2] = 1` for even `N`, `W[k] = 0` for `2k > N` (Marple); `Re z = x` up
  to rounding. Input real, 1-D, finite, not empty; complex input is invalid. **(implemented)**
- **Frequency shifter** (`frequency_shift(samples, shift, sample_rate)`, C#
  `Spectral.FrequencyShift`, [ADR 0301](adr/0301-frequency-shift.md)): with
  `z = analytic_signal(x)` and `θ[n] = (2π·shift)·(n/fs)`, `y[n] = Re z[n]·cos θ[n] −
  Im z[n]·sin θ[n]`. Samples as for `analytic_signal`; finite `shift`; finite
  `sample_rate > 0`. **(implemented)**
- **Instantaneous frequency** (`instantaneous_frequency(samples, sample_rate)`, C#
  `Spectral.InstantaneousFrequency`, [ADR 0187](adr/0187-instantaneous-frequency.md)): `f[n] =
  fs/(2π)·atan2(Im w, Re w)`, `w = z[n+1]·conj z[n]`, `z` the analytic signal; `N − 1` values in
  Hz in `(−fs/2, fs/2]`, no unwrapping; undefined where `z` is zero. Analytic-signal input rules
  with `N ≥ 2`; `sample_rate` finite and positive. **(implemented)**
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
- **Cross-correlation** (`cross_correlation(x, y)`, C# `Dsp.CrossCorrelation`,
  [ADR 0190](adr/0190-cross-correlation.md)): `r[k] = Σ_n x[n+k]·conj y[n]` for `k = −(M−1) …
  N−1` (`N = len x`, `M = len y`), lag `k` at index `k + M − 1`; `x[n] = y[n − d]` peaks at lag
  `d`. NumPy's `correlate(x, y, "full")`; unscaled. Real and real give real, otherwise
  complex. Both 1-D, finite, not empty. **(implemented)**
- **Linear prediction** (`levinson(r, order)`, C# `Dsp.Levinson`,
  [ADR 0149](adr/0149-levinson-durbin.md)): Levinson-Durbin on an autocorrelation `r` (lags
  `0 … order` used). The prediction-error filter `a`, `a[0] = 1`, `order + 1` taps,
  `e[n] = Σ a[j] x[n−j]`, solves `Σ_j a[j] r[i−j] = 0` for `i = 1 … p` with `r[−k] = conj r[k]`.
  Recursion: `k_m = −(r[m] + Σ_{j<m} a[j] r[m−j]) / E`, `a[j] += k_m conj a[m−j]`, `a[m] = k_m`,
  `E *= 1 − |k_m|²`, from `E = r[0]`. Gives `Levinson(coefficients, reflection, error)`. `r`
  finite with `r[0]` real and positive; `order ≥ 1`; every `|k_m| < 1`. **(implemented)**
- **Burg AR fit** (`burg(samples, order)`, C# `Dsp.Burg`,
  [ADR 0205](adr/0205-burg-fit.md)): the recursion of the Burg AR PSD (ADR 0204), giving
  `Levinson(coefficients, reflection, error)`; real samples give real arrays. Samples finite,
  `1 ≤ order < N`, every `|k_m| < 1` and every error energy positive. `burg_psd` uses it.
  **(implemented)**
- **AR order selection** (`ar_order_selection(samples, max_order)`, C# `Dsp.ArOrderSelection`,
  [ADR 0206](adr/0206-ar-order-selection.md)): Burg errors `σ²_0 = mean |x|²`,
  `σ²_p = σ²_{p−1}(1 − |k_p|²)` for `p = 0 … P`; `FPE_p = σ²_p (N + p + 1)/(N − p − 1)`,
  `AIC_p = N ln σ²_p + 2p`; `fpe_order`/`aic_order` minimize each, lowest order on a tie.
  `1 ≤ max_order ≤ N − 2`; Burg's rules otherwise. **(implemented)**
- **LPC cepstrum** (`lpc_cepstrum(coefficients, error, num_coefficients)`, C# `Dsp.LpcCepstrum`,
  [ADR 0207](adr/0207-lpc-cepstrum.md)): the series `ln(σ/A(z)) = Σ c_n z^−n`, `c_0 = ½ ln error`,
  `c_n = −a_n − (1/n) Σ_{k=1}^{n−1} k c_k a_{n−k}` (`a_j = 0` past the order); returns
  `c_0 … c_{num−1}`, real for real coefficients. `a_0 = 1` exactly, coefficients finite,
  `error > 0`, `num_coefficients ≥ 1`. **(implemented)**
- **Line spectral frequencies** (`line_spectral_frequencies(coefficients)`, C#
  `Dsp.LineSpectralFrequencies`, [ADR 0208](adr/0208-line-spectral-frequencies.md)): `a` padded
  to `p + 2`, `P = a + reverse`, `Q = a − reverse`; `F_P = Σ P_j cos(ω s_j)`,
  `F_Q = Σ Q_j sin(ω s_j)`, `s_j = (p + 1)/2 − j`. Sign changes of `F > 0` on `ω = πi/G`,
  `i = 1 … G − 1`, `G = 256(p + 1)`, bisected on the same test until the midpoint meets an end
  (at most 200 halvings), midpoint returned; `p` angles in `(0, π)`, ascending. Real, finite,
  `a_0 = 1`, `p ≥ 1`; other than `p` roots is `invalid_argument`. **(implemented)**
- **LSF to prediction filter** (`lsf_to_lpc(frequencies)`, C# `Dsp.LsfToLpc`,
  [ADR 0209](adr/0209-lsf-to-lpc.md)): `ω_0, ω_2, …` to `P`, `ω_1, ω_3, …` to `Q`, each as
  `1 − 2 cos ω z^−1 + z^−2`, multiplied in ascending order onto the trivial factors (even `p`:
  `1 + z^−1` in `P`, `1 − z^−1` in `Q`; odd `p`: `1 − z^−2` in `Q`); `a = (P + Q)/2` without its
  last tap. Real, finite, non-empty, strictly ascending in `(0, π)`. **(implemented)**
- **Reflection coefficients and prediction filters** (`reflection_to_lpc(reflection)`,
  `lpc_to_reflection(coefficients)`, C# `Dsp.ReflectionToLpc`, `Dsp.LpcToReflection`,
  [ADR 0210](adr/0210-reflection-conversion.md)): step-up from `a = [1]`,
  `a ← pad(a) + k_m conj reverse(pad(a))`; step-down from `m = p`, `k_m = a_m[m]`,
  `a_{m−1}[j] = (a_m[j] − k_m conj a_m[m−j])/(1 − |k_m|²)`. Every `|k| < 1`; finite, non-empty;
  `a_0 = 1`, order ≥ 1; real in, real out. **(implemented)**
- **Lattice analysis filter** (`lattice_filter(samples, reflection)`, C# `Dsp.LatticeFilter`,
  [ADR 0211](adr/0211-lattice-filter.md)): zero state, `f_0 = b_0 = x`,
  `f_m[n] = f_{m−1}[n] + k_m b_{m−1}[n−1]`, `b_m[n] = b_{m−1}[n−1] + conj k_m f_{m−1}[n]`; returns
  `f_p`, `N` samples, the same as `x` filtered by `reflection_to_lpc(k)`. Finite, non-empty; any
  finite `k`. **(implemented)**
- **Lattice synthesis filter** (`lattice_synthesis(excitation, reflection)`, C#
  `Dsp.LatticeSynthesis`, [ADR 0212](adr/0212-lattice-synthesis.md)): zero state; per sample
  `f_p = e[n]`, for `m = p … 1` `f_{m−1} = f_m − k_m b_{m−1}[n−1]`,
  `b_m[n] = b_{m−1}[n−1] + conj k_m f_{m−1}`; `y[n] = b_0[n] = f_0`. It is `1/A(z)` and inverts
  the analysis lattice. Rules as the analysis lattice. **(implemented)**
- **Spectral flatness of an AR model** (`ar_spectral_flatness(reflection)`, C#
  `Dsp.ArSpectralFlatness`, [ADR 0213](adr/0213-ar-spectral-flatness.md)): `Π (1 − |k_m|²)`, the
  geometric over the arithmetic mean of `σ²/|A|²`; in `(0, 1]`. Finite, non-empty, every
  `|k| < 1`. **(implemented)**
- **Autocorrelation of an AR model** (`reflection_to_autocorrelation(reflection, power, lags)`, C#
  `Dsp.ReflectionToAutocorrelation`, [ADR 0214](adr/0214-reflection-to-autocorrelation.md)):
  `r[0] = power`, `E = power`, `a = [1]`; for `m = 1 … lags`, `s = Σ_{j≥1} a_j r[m−j]`;
  `r[m] = −k_m E − s` then step up `a` and `E ← E(1 − |k_m|²)` while `m ≤ p`, else `r[m] = −s`.
  Inverts `levinson`. Returns `lags + 1` values; finite non-empty `k`, every `|k| < 1`; positive
  finite power; integer `lags ≥ 0`. **(implemented)**
- **Log-area ratios** (`reflection_to_lar(reflection)`, `lar_to_reflection(lar)`, C#
  `Dsp.ReflectionToLar`, `Dsp.LarToReflection`, [ADR 0215](adr/0215-log-area-ratios.md)):
  `g = ln((1 + k)/(1 − k)) = 2 atanh k`, `k = tanh(g/2)`. Real, finite, non-empty; every
  `|k| < 1`; any finite `g`. **(implemented)**
- **Inverse sine coefficients** (`reflection_to_arcsine(reflection)`,
  `arcsine_to_reflection(arcsine)`, C# `Dsp.ReflectionToArcsine`, `Dsp.ArcsineToReflection`,
  [ADR 0216](adr/0216-arcsine-coefficients.md)): `θ = arcsin k` in radians, `k = sin θ`. Real,
  finite, non-empty; every `|k| < 1`, every `|θ| < π/2`. **(implemented)**
- **Itakura-Saito distance between AR models** (`itakura_saito(reference, reference_error, test,
  test_error)`, C# `Dsp.ItakuraSaito`, [ADR 0217](adr/0217-itakura-saito.md)):
  `mean (S_r/S_t − ln(S_r/S_t) − 1)` with `S = σ²/|A|²`, in closed form
  `q/σ_t² − ln(σ_r²/σ_t²) − 1`, `q = Σ_{i,j} a_t[i] conj a_t[j] r_r[j−i]`, `r_r` the reference
  model autocorrelation, `r[−m] = conj r[m]`. Filters finite, `a[0] = 1`, order ≥ 0, minimum
  phase; errors positive and finite. **(implemented)**
- **Cepstral distance between AR models** (`cepstral_distance(reference, test, num_coefficients)`,
  C# `Dsp.CepstralDistance`, [ADR 0218](adr/0218-cepstral-distance.md)):
  `sqrt(Σ_{n=1}^{L} |c_r[n] − c_t[n]|²)` with the LPC cepstra of `1/A`; `c_0` left out, so gain
  is ignored. Filters finite, `a[0] = 1`, order ≥ 0, minimum phase; `L ≥ 1`. **(implemented)**
- **Bandwidth expansion** (`bandwidth_expansion(coefficients, factor)`, C#
  `Dsp.BandwidthExpansion`, [ADR 0219](adr/0219-bandwidth-expansion.md)): `a_j γʲ`, i.e.
  `A(z/γ)`, every root `p → γp`. Finite, non-empty coefficients, any `a_0`; real
  `0 < γ ≤ 1`; output dtype follows input. **(implemented)**
- **Autocorrelation of a prediction-error filter** (`lpc_to_autocorrelation(coefficients, error,
  lags)`, C# `Dsp.LpcToAutocorrelation`, [ADR 0220](adr/0220-lpc-to-autocorrelation.md)):
  `k = lpc_to_reflection(a)`, `r = reflection_to_autocorrelation(k, σ²/Π(1 − |k|²), lags)`;
  order 0 gives `[σ², 0, …]`. Filter finite, `a[0] = 1`, minimum phase; error positive and
  finite; integer `lags ≥ 0`. **(implemented)**
- **Schur recursion** (`schur(r, order)`, C# `Dsp.Schur`, [ADR 0221](adr/0221-schur.md)):
  `u = v = r`, `E = r[0]`; per step `k = −u[m]/E`, `u'[i] = u[i] + k v[i−1]`,
  `v'[i] = v[i−1] + conj(k) u[i]`, `E ← E(1 − |k|²)`. Returns `(reflection, error)`, equal to
  `levinson`'s. Same rules as `levinson`. **(implemented)**
- **Cepstrum to prediction filter** (`cepstrum_to_lpc(cepstrum, order)`, C#
  `Dsp.CepstrumToLpc`, [ADR 0222](adr/0222-cepstrum-to-lpc.md)): `a_0 = 1`,
  `a_n = −c_n − (1/n) Σ_{k=1}^{n−1} k c_k a_{n−k}`; `c_0` unused (the error is `exp(2c_0)`).
  Finite cepstrum, at least `order + 1` values; integer `order ≥ 1`; output dtype follows
  input. **(implemented)**
- **Lagrange fractional-delay FIR** (`lagrange_fir(delay, order)`, C# `Dsp.LagrangeFir`,
  [ADR 0225](adr/0225-lagrange-fir.md)): `h[k] = Π_{m≠k} (D − m)/(k − m)`, `k, m = 0 … N`, product
  in increasing `m`; `D` from tap 0, `y[n] = Σ h[k] x[n−k] ≈ x[n − D]`; exact for polynomials of
  degree `≤ N`. Finite `D` (best near `N/2`), integer `order ≥ 1`. **(implemented)**
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
- **Gammatone** (`gammatone(center_frequency, sample_rate, length, *, order=4,
  bandwidth_factor=1.019)`, C# `Dsp.Gammatone`, [ADR 0161](adr/0161-gammatone.md)): taps
  `h[n] = g(n/fs)/G`, `g(t) = t^(N−1)·exp(−2π b ERB(f_c) t)·cos(2π f_c t)` (`t^0 = 1`), `ERB`
  from `erb_bandwidth`, `G = |Σ g(n/fs) e^(−j 2π f_c n/fs)|` so the gain at `f_c` is 1; `G ≤ 0`
  is an error. `fs` finite and positive, `0 < f_c < fs/2`, `length ≥ 1`, `order ≥ 1`, `b`
  finite and positive. **(implemented)**

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
- **Thiran allpass** (`thiran_allpass(delay, order)`, C# `Dsp.ThiranAllpass`,
  [ADR 0227](adr/0227-thiran-allpass.md)): the denominator `a`, `a[0] = 1`, of
  `H(z) = z^(−N) A(1/z)/A(z)` (numerator `a` reversed); with `N = order`, `D = delay`, `a_0 = 1`,
  for `k ≥ 1` `a_k = (−1)^k C(N, k) Π_{n=0}^{N} (D − N + n)/(D − N + k + n)`, `C(N, k)` as
  `Π_{i=1}^{k} (N − k + i)/i`, then the ratios in increasing `n`. DC group delay exactly `D`,
  maximally flat; `D = N` gives `[1, 0, …, 0]`. Finite `D > N − 1` (stable), integer
  `order ≥ 1`. **(implemented)**
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
- **Weighting filters** (`a_weighting_sos(sample_rate)`, `c_weighting_sos(sample_rate)`, C#
  `Dsp.AWeightingSos`, `Dsp.CWeightingSos`, [ADR 0165](adr/0165-weighting-filters.md)): the
  analog A and C curves (Frequency weightings, ADR 0164; `ω_k = 2π f_k`) by the bilinear
  transform `s = K(1 − z⁻¹)/(1 + z⁻¹)`, `K = 2fs`, no prewarping. Each section is the product
  of two first-order factors: high-pass `s/(s + ω)` → `b = [K, −K]/(K + ω)`, low-pass
  `ω/(s + ω)` → `b = [ω, ω]/(K + ω)`, both `a = [1, (ω − K)/(K + ω)]`. A: `HP ω1·HP ω1`, `HP
  ω2·HP ω3`, `LP ω4·LP ω4`; C: `HP ω1·HP ω1`, `LP ω4·LP ω4`. The first section's `b` is divided
  by `Π Ω/√(Ω² + ω²)` (high-pass) and `ω/√(Ω² + ω²)` (low-pass) at `Ω = K tan(π·1000/fs)`, so
  the gain at 1 kHz is exactly 1. `fs` finite and `> 2000`. **(implemented)**
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
- **CIC decimator** (`cic_taps(factor, stages, *, delay=1)`,
  `cic_decimate(samples, factor, stages, *, delay=1)`, C# `Dsp.CicTaps`, `Dsp.CicDecimate`,
  [ADR 0229](adr/0229-cic-decimator.md)): with `R = factor`, `N = stages`, `M = delay`, `h` is the
  `N`-fold convolution of `R·M` ones (`N(RM − 1) + 1` taps, sum `(RM)^N`, unnormalized);
  `y[k] = Σ_m h[m] x[kR − m]`, `k = 0 … ⌈L/R⌉ − 1`, `x` zero before 0, which equals `N`
  integrators, every `R`th sample from 0, then `N` combs of delay `M`. Computed as that FIR.
  Integers `≥ 1`, `stages ≤ 64`, `(RM)^N ≤ 2^53`; samples finite and non-empty.
  **(implemented)**
- **CIC interpolator** (`cic_interpolate(samples, factor, stages, *, delay=1)`, C#
  `Dsp.CicInterpolate`, [ADR 0230](adr/0230-cic-interpolator.md)): `u[kR] = x[k]`, other samples
  0; `y[n] = Σ_m h[m] u[n − m]` for `n = 0 … LR − 1` with `h = cic_taps(R, N, M)`, the sum over
  `m ≡ n (mod R)`, `m ≤ n`, in increasing `m`. Equals `N` combs at the low rate, zero-stuffing,
  then `N` integrators. Unnormalized (a constant settles to `(RM)^N/R`). Rules as the CIC
  decimator; samples finite and non-empty. **(implemented)**
- **CIC droop compensator** (`cic_compensator(factor, stages, num_taps, cutoff, sample_rate, *,
  delay=1)`, C# `Dsp.CicCompensator`, [ADR 0232](adr/0232-cic-compensator.md)): `sample_rate` is
  the low rate; droop `A(f) = |sin(πMf)/(RM sin(πf/R))|^N`, `A(0) = 1`, `f` in cycles per low-rate
  sample. Type-1 frequency sampling, no window: `T` odd, `c = (T−1)/2`, `D_j = 1/A(j/T)` where
  `j/T ≤ cutoff/sample_rate`, else 0, `j = 0 … c`; `h[n] = (D_0 + 2 Σ_{j=1}^{c} D_j cos(2πj(n−c)/T))/T`.
  Rules: integers `≥ 1`, `stages ≤ 64`, odd `num_taps`, `sample_rate` finite and positive,
  `0 < cutoff ≤ sample_rate/(2M)`, every `D_j` finite. **(implemented)**
- **Savitzky–Golay** (`savgol_coefficients(length, order, *, derivative=0, position=0)`,
  `savgol_filter(samples, length, order, *, derivative=0)`, C# `Dsp.SavgolCoefficients`,
  `Dsp.SavgolFilter`, [ADR 0233](adr/0233-savitzky-golay.md)): `h = (length−1)/2`; `c[k+h]`,
  `k = −h … h`, gives the `derivative`-th derivative (per sample) at offset `position` of the
  degree-`order` least-squares polynomial through `(k, x[k])`; applied as a correlation,
  `Σ_k c[k+h] x[n+k]`. Computed with `t = k/s`, `s = max(h, 1)`, modified Gram–Schmidt `A = QR`,
  `Rᵀz = v`, `c = Qz`. Filter: centre coefficients inside; the first and last `h` outputs evaluate
  the fit to the first or last `length` samples at their own offsets. Rules: odd `length ≥ 1`,
  `0 ≤ order < length`, `0 ≤ derivative ≤ order`, `|position| ≤ h`; samples real, finite, at least
  `length`. **(implemented)**
- **Running median filter** (`median_filter(samples, length)`, C# `Dsp.MedianFilter`,
  [ADR 0234](adr/0234-median-filter.md)): `h = (length−1)/2`; `y[n]` = median of
  `x[n−w … n+w]`, `w = min(h, n, L−1−n)` (a symmetric window that shrinks at the ends; always an
  odd count, so `y[0] = x[0]`, `y[L−1] = x[L−1]`). Odd `length ≥ 1`; samples real, finite,
  non-empty, any length. **(implemented)**
- **Hampel filter** (`hampel_filter(samples, length, threshold=3.0)`, C# `Dsp.HampelFilter`,
  [ADR 0235](adr/0235-hampel-filter.md)): the windows of the running median filter; `m_n` the
  window median, `MAD_n` the median of `|x_j − m_n|`; `y[n] = m_n` if
  `|x[n] − m_n| > (threshold·κ)·MAD_n` (strict), else `x[n]`, with `κ = 1/Φ⁻¹(3/4) =
  1.482602218505602`. Odd `length ≥ 1`, finite `threshold ≥ 0`; samples real, finite, non-empty.
  **(implemented)**
- **DC blocker** (`dc_blocker(samples, pole)`, C# `Dsp.DcBlocker`,
  [ADR 0236](adr/0236-dc-blocker.md)): `y[n] = (x[n] − x[n−1]) + p·y[n−1]`, `x[−1] = y[−1] = 0`
  (from rest; `H(z) = (1 − z⁻¹)/(1 − p z⁻¹)`). Finite `0 ≤ pole < 1`; samples finite, non-empty,
  real or complex. **(implemented)**
- **Comb filter** (`comb_filter(samples, delay, gain, *, feedback=False)`, C# `Dsp.CombFilter`,
  [ADR 0237](adr/0237-comb-filter.md)): `x`, `y` zero before 0; feedforward
  `y[n] = x[n] + g·x[n−D]`; feedback `y[n] = x[n] + g·y[n−D]`; output the input's length. Integer
  `delay ≥ 1`, finite `gain` (`|gain| < 1` for feedback); samples finite, non-empty, real or
  complex. **(implemented)**
- **Envelope follower** (`envelope_follower(samples, attack, release)`, C#
  `Dsp.EnvelopeFollower`, [ADR 0238](adr/0238-envelope-follower.md)): `r[n] = |x[n]|`,
  `e[−1] = 0`, `e[n] = r[n] + c·(e[n−1] − r[n])` with `c = attack` if `r[n] > e[n−1]`, else
  `release`; coefficients per sample (`exp(−1/(τ fs))` for a time constant `τ`). Finite
  coefficients in `[0, 1)`; samples finite, non-empty, real or complex; output real.
  **(implemented)**
- **Moving RMS** (`moving_rms(samples, length)`, C# `Dsp.MovingRms`,
  [ADR 0239](adr/0239-moving-rms.md)): `y[n] = sqrt((1/N) Σ_{k=n−N+1}^{n} |x[k]|²)`, `x` zero
  before 0 (from rest: always divided by `N`); summed directly, oldest first. Integer
  `length ≥ 1`; samples finite, non-empty, real or complex; output real. **(implemented)**
- **Schroeder allpass section** (`allpass_comb(samples, delay, gain)`, C# `Dsp.AllpassComb`,
  [ADR 0240](adr/0240-allpass-comb.md)): `y[n] = −g x[n] + x[n−D] + g y[n−D]`, added left to
  right, zero before 0; `H(z) = (−g + z^−D)/(1 − g z^−D)`, `h[0] = −g`,
  `h[kD] = (1 − g²) g^(k−1)`. Integer `delay ≥ 1`, finite `|g| < 1`; samples finite, non-empty,
  real or complex; output the same kind. **(implemented)**
- **Moving average** (`moving_average(samples, length)`, C# `Dsp.MovingAverage`,
  [ADR 0241](adr/0241-moving-average.md)): `y[n] = (1/N) Σ_{k=n−N+1}^{n} x[k]`, `x` zero before
  0 (from rest: always divided by `N`); summed directly, oldest first, then divided. Integer
  `length ≥ 1`; samples finite, non-empty, real or complex; output the same kind.
  **(implemented)**
- **Slew-rate limiter** (`slew_limiter(samples, rise, fall)`, C# `Dsp.SlewLimiter`,
  [ADR 0242](adr/0242-slew-limiter.md)): `y[−1] = 0`, `d = x[n] − y[n−1]`;
  `y[n] = y[n−1] + rise` if `d > rise`, `y[n−1] − fall` if `d < −fall`, else `x[n]` exactly.
  Finite `rise, fall > 0`; samples real, finite, non-empty. **(implemented)**
- **Peak hold** (`peak_hold(samples, hold, release)`, C# `Dsp.PeakHold`,
  [ADR 0243](adr/0243-peak-hold.md)): `r = |x[n]|`, from `p = 0, c = 0`: if `r ≥ p` then
  `p = r, c = 0`; else if `c < hold` then `c += 1`; else `p = max(release·p, r)` (`c` kept).
  Output `p`. Integer `hold ≥ 0`, finite `release` in `[0, 1)`; samples finite, non-empty, real or
  complex; output real. **(implemented)**
- **Schmitt trigger** (`schmitt_trigger(samples, low, high)`, C# `Dsp.SchmittTrigger`,
  [ADR 0244](adr/0244-schmitt-trigger.md)): state from 0; `x[n] > high` → 1, `x[n] < low` → 0,
  otherwise kept (strict: on a threshold keeps the state); output the state as `uint8` / `byte`.
  Finite `low < high`; samples real, finite, non-empty. **(implemented)**
- **Sample-and-hold** (`sample_and_hold(samples, period, *, offset=0)`, C#
  `Dsp.SampleAndHold`, [ADR 0245](adr/0245-sample-and-hold.md)):
  `y[n] = x[offset + P⌊(n − offset)/P⌋]` for `n ≥ offset`, 0 before (from rest); exact copies.
  Integer `period ≥ 1`, integer `offset` in `[0, period)`; samples finite, non-empty, real or
  complex; output the same kind. **(implemented)**
- **Dead zone** (`dead_zone(samples, width)`, C# `Dsp.DeadZone`,
  [ADR 0246](adr/0246-dead-zone.md)): `y = 0` if `|x| ≤ width`, `x − width` above, `x + width`
  below (the soft threshold; memoryless, continuous). Finite `width ≥ 0`; samples real, finite,
  non-empty. **(implemented)**
- **Uniform quantizer** (`quantize(samples, step, *, levels=None)`, C# `Dsp.Quantize`,
  [ADR 0247](adr/0247-quantize.md)): mid-tread `k = round(x/step)` with round half to even
  (`np.rint`, `MidpointRounding.ToEven`), `y = step·k`; with odd `levels = L`, `k` clamped to
  `±(L − 1)/2` first. Complex: each part separately. Finite `step > 0`; `levels` odd `≥ 1` or
  none; samples finite, non-empty; output the same kind. **(implemented)**
- **μ-law companding** (`mu_law_compress(samples, mu=255.0)`, `mu_law_expand`, C#
  `Dsp.MuLawCompress`, `Dsp.MuLawExpand`, [ADR 0248](adr/0248-mu-law.md)): compress
  `sign(x)·log1p(μ|x|)/log1p(μ)`, expand `sign(y)·expm1(|y|·log1p(μ))/μ` (`sign(0) = 0`; the
  continuous curve, not G.711 segments). Finite `μ > 0`; samples real, finite, non-empty, in
  `[−1, 1]`. **(implemented)**
- **A-law companding** (`a_law_compress(samples, a=87.6)`, `a_law_expand`, C#
  `Dsp.ALawCompress`, `Dsp.ALawExpand`, [ADR 0249](adr/0249-a-law.md)): with `L = 1 + ln A`,
  compress `A|x|/L` below `|x| = 1/A`, else `(1 + ln(A|x|))/L`; expand `|y|·L/A` below
  `|y| = 1/L`, else `exp(|y|·L − 1)/A`; the knee goes to the log branch; sign last
  (`sign(0) = 0`). Finite `a ≥ 1`; samples real, finite, non-empty, in `[−1, 1]`.
  **(implemented)**
- **Cubic soft clipper** (`soft_clip(samples)`, C# `Dsp.SoftClip`,
  [ADR 0250](adr/0250-soft-clip.md)): `x − x·x·x/3` for `|x| < 1`; `±2/3` (the nearest double)
  for `|x| ≥ 1` (odd; value and slope continuous at `±1`). Samples real, finite, non-empty.
  **(implemented)**
- **Hard clipper** (`hard_clip(samples, limit)`, C# `Dsp.HardClip`,
  [ADR 0251](adr/0251-hard-clip.md)): real `min(max(x, −limit), limit)`; complex `x` if
  `|x| ≤ limit`, else `x·(limit/|x|)` (the phase kept). Finite `limit ≥ 0`; samples finite,
  non-empty; output the same kind. **(implemented)**
- **Chebyshev waveshaper** (`chebyshev_shaper(samples, weights)`, C# `Dsp.ChebyshevShaper`,
  [ADR 0321](adr/0321-chebyshev-shaper.md)): `y = Σ_k w_k·T_k(x)` by Clenshaw:
  `b_k = w_k + (2·x·b_{k+1} − b_{k+2})` for `k = K … 1` from `b_{K+1} = b_{K+2} = 0`, then
  `y = w_0 + (x·b_1 − b_2)`. Real, non-empty, finite samples in `[−1, 1]`; real, non-empty,
  finite weights. **(implemented)**
- **Sine wavefolder** (`sine_fold(samples, drive)`, C# `Dsp.SineFold`,
  [ADR 0323](adr/0323-sine-fold.md)): `k = (π/2)·drive`, `y = sin(k·x)`. Real, non-empty, finite
  samples; finite positive `drive`. **(implemented)**
- **Wavefolder** (`wavefold(samples, limit)`, C# `Dsp.Wavefold`,
  [ADR 0252](adr/0252-wavefold.md)): reflect about `±L` until inside; computed as `u = x + L`,
  `t = u − 4L·⌊u/(4L)⌋`, `y = L − |t − 2L|`, in that order, no library modulo. Finite
  `limit > 0`; samples real, finite, non-empty. **(implemented)**
- **Rectifier** (`rectify(samples, *, full=True)`, C# `Dsp.Rectify`,
  [ADR 0253](adr/0253-rectify.md)): full wave `|x|`; half wave `x` if `x > 0`, else `0` (`−0`
  gives `+0`). Samples real, finite, non-empty. **(implemented)**
- **Compressor gain computer** (`compressor_gain(level_db, threshold_db, ratio, *,
  knee_db=0.0)`, C# `Dsp.CompressorGain`, [ADR 0254](adr/0254-compressor-gain.md)): with
  `d = x − T`, `s = 1/ratio − 1`, `W = knee_db`: `0` if `2d < −W`; `s·d` if `2d > W`; else
  `s·q·q/(2W)`, `q = d + W/2` (edges in the knee; `W = 0` gives 0 at `d = 0`). Gain in dB, `≤ 0`. Finite
  `threshold_db`; finite `ratio ≥ 1`; finite `knee_db ≥ 0`; levels real, finite, non-empty.
  **(implemented)**
- **Noise gate** (`noise_gate(samples, threshold, *, hold=0)`, C# `Dsp.NoiseGate`,
  [ADR 0255](adr/0255-noise-gate.md)): counter `c` from `hold + 1`; `|x[n]| > threshold` sets
  `c = 0`, otherwise `c` rises by 1 (capped at `hold + 1`); `y[n] = x[n]` if `c ≤ hold`, else 0.
  Strict comparison; complex by magnitude. Finite `threshold ≥ 0`; integer `hold ≥ 0`; samples
  finite, non-empty; output the same kind. **(implemented)**
- **Downward-expander gain computer** (`expander_gain(level_db, threshold_db, ratio, *,
  knee_db=0.0)`, C# `Dsp.ExpanderGain`, [ADR 0256](adr/0256-expander-gain.md)): with
  `d = x − T`, `s = ratio − 1`, `W = knee_db`: `0` if `2d > W`; `s·d` if `2d < −W`; else
  `q = d − W/2`, `−(s·q·q/(2W))` (edges in the knee; `W = 0` gives 0 at `d = 0`). Gain in dB,
  `≤ 0`. Rules as the compressor gain computer. **(implemented)**
- **Feed-forward compressor** (`compress(samples, threshold_db, ratio, attack, release, *,
  knee_db=0.0, makeup_db=0.0)`, C# `Dsp.Compress`, [ADR 0257](adr/0257-compress.md)): `e` =
  envelope follower (ADR 0238); `g = compressor_gain(20·log10 e)` (ADR 0254), `g = 0` where
  `e = 0`; `y = x·10^((g + makeup_db)/20)`. Rules of both parts, plus finite `makeup_db`; real or
  complex, the same kind out. **(implemented)**
- **Downward expander** (`expand(samples, threshold_db, ratio, attack, release, *, knee_db=0.0,
  makeup_db=0.0)`, C# `Dsp.Expand`, [ADR 0258](adr/0258-expand.md)): the feed-forward
  compressor's chain with `g = expander_gain(20·log10 e)` (ADR 0256), `g = 0` where `e = 0`.
  Same rules; real or complex, the same kind out. **(implemented)**
- **Tanh saturator** (`saturate(samples, drive)`, C# `Dsp.Saturate`,
  [ADR 0259](adr/0259-saturate.md)): `y = tanh(drive·x)/tanh(drive)`, in that order. Finite
  `drive > 0`; samples real, finite, non-empty. **(implemented)**
- **Ring modulator** (`ring_modulate(samples, frequency, sample_rate, *, phase=0.0)`, C#
  `Dsp.RingModulate`, [ADR 0260](adr/0260-ring-modulate.md)): `y[n] = x[n]·cos((2π·f)·(n/fs) + φ)`,
  the argument built as for `tone`. Finite `sample_rate > 0`; finite `frequency` and `phase`;
  samples finite, non-empty; real or complex, the same kind out. **(implemented)**
- **Tremolo** (`tremolo(samples, rate, depth, sample_rate)`, C# `Dsp.Tremolo`,
  [ADR 0261](adr/0261-tremolo.md)): `c = cos((2π·rate)·(n/fs))`; `g = 1 − depth·(1 − c)/2`;
  `y = x·g`. Finite `rate`; `depth` in `[0, 1]`; finite `sample_rate > 0`; samples finite,
  non-empty; real or complex, the same kind out. **(implemented)**
- **Fades** (`fade(samples, fade_in, fade_out, *, shape="linear")`, C# `Dsp.Fade` with
  `FadeShape`, [ADR 0262](adr/0262-fade.md)): ramp `r(t) = t` (linear) or `(1 − cos(π·t))/2`
  (cosine); gain 1, times `r(n/Lᵢ)` for `n < Lᵢ`, times `r(k/Lₒ)` for `k = N−1−n < Lₒ`; first
  and last ramp samples 0. Integer `fade_in`, `fade_out` in `[0, N]`; samples finite, non-empty;
  real or complex, the same kind out. **(implemented)**
- **Crossfade** (`crossfade(a, b, overlap, *, shape="linear")`, C# `Dsp.Crossfade`,
  [ADR 0263](adr/0263-crossfade.md)): `a[:Nₐ−L]`, then for `k < L`, `t = (k+1)/(L+1)`,
  `w = r(t)` (the fade ramp), `a[Nₐ−L+k]·(1 − w) + b[k]·w`, then `b[L:]`. Integer `overlap` in
  `[0, min(Nₐ, N_b)]`; inputs finite, non-empty; complex if either is. **(implemented)**
- **Mid/side coding** (`mid_side_encode(left, right)`, `mid_side_decode(mid, side)`, C#
  `Dsp.MidSideEncode`, `Dsp.MidSideDecode`, [ADR 0264](adr/0264-mid-side.md)):
  `mid = (left + right)/2`, `side = (left − right)/2`; `left = mid + side`,
  `right = mid − side`. Inputs real, finite, non-empty, equal length. **(implemented)**
- **Panner** (`pan(samples, position, *, law="constant_power")`, C# `Dsp.Pan`,
  [ADR 0265](adr/0265-pan.md)): constant power `θ = (position + 1)·(π/4)`, `gL = cos θ`,
  `gR = sin θ`; linear `gL = (1 − position)/2`, `gR = (1 + position)/2`; `left = x·gL`,
  `right = x·gR`. `position` in `[−1, 1]`; samples real, finite, non-empty. **(implemented)**
- **Bitcrusher** (`bitcrush(samples, bits, *, hold=1)`, C# `Dsp.Bitcrush`,
  [ADR 0266](adr/0266-bitcrush.md)): `quantize(sample_and_hold(x, hold), 2^(1−bits),
  levels=2^bits − 1)`, so outputs lie on `k·2^(1−bits)`, `|k| ≤ 2^(bits−1) − 1`. Integer `bits`
  from 2 to 24, integer `hold ≥ 1`; samples real, finite, non-empty. **(implemented)**
- **Stereo width** (`stereo_width(left, right, width)`, C# `Dsp.StereoWidth`,
  [ADR 0267](adr/0267-stereo-width.md)): `m = (left + right)/2`, `s = ((left − right)/2)·width`,
  `left' = m + s`, `right' = m − s`. Finite `width ≥ 0`; inputs real, finite, non-empty, equal
  length. **(implemented)**
- **Peak normalization** (`normalize_peak(samples, peak=1.0)`, C# `Dsp.NormalizePeak`,
  [ADR 0268](adr/0268-normalize-peak.md)): `g = peak / max|x|`, `y = x·g` (complex: part by
  part). Finite `peak > 0`; samples finite, non-empty, not all zero; output the same kind.
  **(implemented)**
- **Lookahead peak limiter** (`limit(samples, threshold, lookahead, release)`, C#
  `Dsp.Limit`, [ADR 0269](adr/0269-limit.md)): `c[n] = min(1, T/|x[n]|)` (1 at 0),
  `a[n] = min c[n … n + lookahead]` (clamped at the end), `g[−1] = 1`, `g[n] = a[n]` if
  `a[n] < g[n−1]`, else `a[n] + release·(g[n−1] − a[n])`; `y = x·g` (complex: part by part).
  Finite `threshold > 0`, integer `lookahead ≥ 0`, `release` in `[0, 1)`; samples finite,
  non-empty. **(implemented)**
- **Auto-panner** (`auto_pan(samples, rate, depth, sample_rate, *, law="constant_power")`,
  C# `Dsp.AutoPan`, [ADR 0270](adr/0270-auto-pan.md)): the panner at
  `p[n] = depth·cos((2π·rate)·(n/fs))`, per sample. Finite `rate`, `depth` in `[0, 1]`, finite
  `sample_rate > 0`; samples real, finite, non-empty. **(implemented)**
- **Vibrato** (`vibrato(samples, delay, depth, rate, sample_rate)`, C# `Dsp.Vibrato`,
  [ADR 0271](adr/0271-vibrato.md)): `d[n] = delay + depth·cos((2π·rate)·(n/fs))` samples,
  `p = n − d`, `i = ⌊p⌋`, `f = p − i`, `y = x[i]·(1 − f) + x[i+1]·f` with `x[k < 0] = 0`
  (complex: part by part). Finite `delay ≥ 0`, `depth` in `[0, delay]`, finite `rate`, finite
  `sample_rate > 0`; samples finite, non-empty. **(implemented)**
- **Flanger** (`flanger(samples, delay, depth, rate, sample_rate, mix)`, C# `Dsp.Flanger`,
  [ADR 0272](adr/0272-flanger.md)): `y = x·(1 − mix) + v·mix` with `v` the vibrato (complex:
  part by part). The vibrato's rules; finite `mix` in `[0, 1]`. **(implemented)**
- **Chorus** (`chorus(samples, delay, depth, rate, sample_rate, voices, mix)`, C#
  `Dsp.Chorus`, [ADR 0273](adr/0273-chorus.md)): voice `k < V` is the vibrato with delay
  `delay + depth·cos((2π·rate)·(n/fs) + (2π·k)/V)`; `w = (v₀ + … + v_{V−1})/V` in voice order;
  `y = x·(1 − mix) + w·mix` (complex: part by part). The vibrato's rules; integer `voices ≥ 1`;
  finite `mix` in `[0, 1]`. **(implemented)**
- **Phaser** (`phaser(samples, stages, low, high, rate, sample_rate, mix)`, C# `Dsp.Phaser`,
  [ADR 0274](adr/0274-phaser.md)): `fc[n] = low + (high − low)·((1 − cos((2π·rate)·(n/fs)))/2)`,
  `t = tan((π·fc)/fs)`, `c = (t − 1)/(t + 1)`; `stages` first-order allpasses
  `y[n] = c[n]·x[n] + x[n−1] − c[n]·y[n−1]` in series from rest (complex: part by part);
  `y = x·(1 − mix) + w·mix`. Integer `stages ≥ 1`; `0 < low ≤ high < fs/2`; finite `rate`;
  finite `mix` in `[0, 1]`. **(implemented)**
- **Ping-pong delay** (`ping_pong_delay(samples, delay, feedback, mix)`, C#
  `Dsp.PingPongDelay`, [ADR 0275](adr/0275-ping-pong-delay.md)): a `LeftRight` from real mono
  samples. `a[n] = x[n − D] + g·b[n − D]`, then `b[n] = g·a[n − D]`, zero before time 0;
  `left = x·(1 − mix) + a·mix`, `right = x·(1 − mix) + b·mix`. Integer `delay ≥ 1`; finite
  `|feedback| < 1`; finite `mix` in `[0, 1]`. **(implemented)**
- **Haas widener** (`haas(samples, delay, *, side="right")`, C# `Dsp.Haas` with
  `StereoSide`, [ADR 0276](adr/0276-haas.md)): a `LeftRight` from real mono samples; the named
  side is `x[n − delay]` (0 before time 0), the other side is `x`. Integer `delay ≥ 0`; `side`
  `"left"` or `"right"`. **(implemented)**
- **Stereo balance** (`balance(left, right, position)`, C# `Dsp.Balance`,
  [ADR 0277](adr/0277-balance.md)): `left·gL`, `right·gR` with `gL = 1 − p` for `p > 0` else 1
  and `gR = 1 + p` for `p < 0` else 1. Finite `position` in `[−1, 1]`; real, finite,
  non-empty channels of equal length. **(implemented)**
- **Sidechain compressor** (`duck(samples, key, threshold_db, ratio, attack, release, *,
  knee_db=0, makeup_db=0)`, C# `Dsp.Duck`, [ADR 0278](adr/0278-duck.md)): the feed-forward
  compressor with its envelope taken from the real `key`; the factor
  `10^((g + makeup_db)/20)` multiplies `samples` (complex: part by part). The compressor's
  rules; `samples` finite and as long as `key`. **(implemented)**
- **State-variable filter** (`svf(samples, cutoff, q, sample_rate, *, output="lowpass")`, C#
  `Dsp.Svf` with `SvfOutput`, [ADR 0279](adr/0279-svf.md)): the TPT form. `g = tan((π·cutoff)/fs)`,
  `k = 1/q`, `a1 = 1/(1 + g·(g + k))`, `a2 = g·a1`, `a3 = g·a2`; from rest, `v3 = x − ic2`,
  `v1 = a1·ic1 + a2·v3`, `v2 = ic2 + a2·ic1 + a3·v3`, `ic1 = 2·v1 − ic1`, `ic2 = 2·v2 − ic2`.
  Low `v2`, band `v1` (peak gain `q`), high `x − k·v1 − v2`, notch `x − k·v1`; complex part by
  part. `0 < cutoff < fs/2`, finite `q > 0`. **(implemented)**
- **Auto-wah** (`auto_wah(samples, low, high, q, attack, release, sample_rate, mix)`, C#
  `Dsp.AutoWah`, [ADR 0280](adr/0280-auto-wah.md)): `e = envelope_follower(samples, attack,
  release)`, `fc = low + (high − low)·min(e, 1)`, `g = tan((π·fc)/fs)` per sample; the SVF
  recursion with `a1`, `a2`, `a3` recomputed each sample and the state carried; wet `k·v1`;
  `y = x·(1 − mix) + wet·mix` (complex: part by part, one envelope). `0 < low ≤ high < fs/2`;
  finite `q > 0`; finite `mix` in `[0, 1]`. **(implemented)**
- **Transient shaper** (`transient_shaper(samples, fast, slow, amount)`, C#
  `Dsp.TransientShaper`, [ADR 0281](adr/0281-transient-shaper.md)): `ef` and `es` are the
  envelope follower with `(fast, fast)` and `(slow, slow)`; `g = (ef/es)^amount`, 1 where either
  is 0; `y = x·g` (complex part by part). Finite `fast`, `slow` in `[0, 1)`; finite `amount`.
  **(implemented)**
- **Shelving and peaking EQ** (`low_shelf`, `high_shelf`, `peaking_eq`, each
  `(frequency, gain_db, q, sample_rate)`, C# `Dsp.LowShelf`, `Dsp.HighShelf`, `Dsp.PeakingEq`,
  [ADR 0282](adr/0282-eq-sections.md)): one section with `a0 = 1`, from `A = 10^(gain_db/40)`,
  `w0 = (2π·frequency)/fs`, `c = cos w0`, `α = sin(w0)/(2q)`. Peaking
  `b = [1 + αA, −2c, 1 − αA]`, `a = [1 + α/A, −2c, 1 − α/A]`; the shelf forms are in the ADR.
  Gain `A²` at DC (low shelf), fs/2 (high shelf) or `w0` (peaking), 1 at the other end(s).
  `0 < frequency < fs/2`, finite `q > 0`, finite `gain_db`. **(implemented)**
- **Tilt EQ** (`tilt_eq(frequency, gain_db, sample_rate)`, C# `Dsp.TiltEq`,
  [ADR 0283](adr/0283-tilt-eq.md)): one section `[b0, b1, 0, 1, a1, 0]` from
  `H(s) = (T·s + 1)/(s + T)`, `T = 10^(gain_db/40)`: with `t = tan((π·frequency)/fs)`,
  `b0 = (T + t)/(1 + T·t)`, `b1 = (t − T)/(1 + T·t)`, `a1 = (T·t − 1)/(1 + T·t)`. Gain `1/T` at
  DC, `T` at fs/2, 1 at the pivot. `0 < frequency < fs/2`; finite `gain_db`. **(implemented)**
- **Linkwitz-Riley crossover** (`linkwitz_riley(order, cutoff, sample_rate)` returning
  `Crossover(low, high)`, C# `Dsp.LinkwitzRiley`, [ADR 0284](adr/0284-linkwitz-riley.md)): with
  `N = order/2`, `low` is the `butterworth_lowpass(N)` sections twice over and `high` the
  `butterworth_highpass(N)` sections twice over, the first `high` section's `b` negated when `N`
  is odd. Both are 1/2 in magnitude at the cutoff; `|low + high| = 1`. Even `order` from 2 to
  2000; the Butterworth cutoff rules. **(implemented)**
- **Two-band splitter** (`crossover_split(samples, order, cutoff, sample_rate)` returning
  `Bands(low, high)`, C# `Dsp.CrossoverSplit`, [ADR 0285](adr/0285-crossover-split.md)): the
  `linkwitz_riley` bands, each run from rest over the real, finite, non-empty samples by
  `IirFilter`; `low + high` is the crossover's all-pass of the input. **(implemented)**
- **De-esser** (`de_esser(samples, cutoff, q, threshold_db, ratio, attack, release,
  sample_rate)`, C# `Dsp.DeEsser`, [ADR 0286](adr/0286-de-esser.md)): `duck(samples, key,
  threshold_db, ratio, attack, release)` with `key = (1/q)·svf(samples, cutoff, q, fs,
  output="bandpass")`; hard knee, no make-up. Real samples; the SVF's and the sidechain
  compressor's rules. **(implemented)**
- **Two-band compressor** (`two_band_compress(samples, order, cutoff, sample_rate,
  low_threshold_db, low_ratio, high_threshold_db, high_ratio, attack, release)`, C#
  `Dsp.TwoBandCompress`, [ADR 0287](adr/0287-two-band-compress.md)): with `b =
  crossover_split(samples, order, cutoff, fs)`, `compress(b.low, low_threshold_db, low_ratio,
  attack, release) + compress(b.high, high_threshold_db, high_ratio, attack, release)`; hard
  knee, no make-up. Real samples; the splitter's and the compressor's rules. **(implemented)**
- **Harmonic exciter** (`exciter(samples, order, cutoff, sample_rate, drive, mix)`, C#
  `Dsp.Exciter`, [ADR 0288](adr/0288-exciter.md)): with `h = crossover_split(samples, order,
  cutoff, fs).high`, `y = x + mix·soft_clip(drive·h)/drive`. Real samples; the splitter's rules;
  `drive` finite and positive; `mix` in [0, 1]. **(implemented)**
- **Octave-up effect** (`octave_up(samples, pole, mix)`, C# `Dsp.OctaveUp`,
  [ADR 0289](adr/0289-octave-up.md)): `wet = dc_blocker(|x|, pole)`, `y = (1 − mix)·x +
  mix·wet`. Real, finite, non-empty samples; `pole` in [0, 1); `mix` in [0, 1].
  **(implemented)**
- **Bass enhancer** (`bass_enhancer(samples, order, cutoff, sample_rate, drive, mix)`, C#
  `Dsp.BassEnhancer`, [ADR 0290](adr/0290-bass-enhancer.md)): with `l = crossover_split(samples,
  order, cutoff, fs).low` and `h = crossover_split(soft_clip(drive·l)/drive, order, cutoff,
  fs).high`, `y = x + mix·h`. Real samples; the splitter's rules; `drive` finite and positive;
  `mix` in [0, 1]. **(implemented)**
- **Octave-down effect** (`octave_down(samples, mix)`, C# `Dsp.OctaveDown`,
  [ADR 0291](adr/0291-octave-down.md)): a sign starting at +1 flips before sample `n ≥ 1` when
  `x[n−1] < 0 ≤ x[n]`; `wet[n] = s·|x[n]|`; `y = (1 − mix)·x + mix·wet`. No hysteresis. Real,
  finite, non-empty samples; `mix` in [0, 1]. **(implemented)**
- **Rotary-speaker effect** (`rotary(samples, order, cutoff, horn_rate, drum_rate, delay, depth,
  tremolo_depth, sample_rate)`, C# `Dsp.Rotary`, [ADR 0292](adr/0292-rotary.md)): with `b =
  crossover_split(samples, order, cutoff, fs)`, `tremolo(vibrato(b.high, delay, depth,
  horn_rate, fs), horn_rate, tremolo_depth, fs) + tremolo(b.low, drum_rate, tremolo_depth, fs)`.
  Real samples; the splitter's, vibrato's and tremolo's rules. **(implemented)**
- **Channel vocoder** (`vocoder(carrier, modulator, bands, low, high, q, attack, release,
  sample_rate)`, C# `Dsp.Vocoder`, [ADR 0293](adr/0293-vocoder.md)): band `k` is centred at
  `f_k = low·(high/low)^((k + 1/2)/bands)` and is `(1/q)·svf(·, f_k, q, fs, "bandpass")`; `y =
  Σ_k C_k·envelope_follower(M_k, attack, release)`. Real, finite, non-empty signals of one
  length; `bands` from 1 to 1000; `0 < low < high < fs/2`. **(implemented)**
- **Slicer** (`slicer(samples, rate, duty, sample_rate)`, C# `Dsp.Slicer`,
  [ADR 0294](adr/0294-slicer.md)): with `t = rate·(n/fs)` and `p = t − floor(t)`, `y[n] = x[n]`
  where `p < duty` and 0 otherwise. Real, finite, non-empty samples; `rate` finite and at least
  0; `duty` in [0, 1]. **(implemented)**
- **Schroeder reverberator** (`schroeder_reverb(samples, combs, comb_gains, allpasses,
  allpass_gain, mix)`, C# `Dsp.SchroederReverb`, [ADR 0295](adr/0295-schroeder-reverb.md)):
  `w = (Σ_k comb_filter(x, combs[k], comb_gains[k], feedback=True))/K`, summed in order and
  divided once, then `allpass_comb(·, d, allpass_gain)` for each `d` of `allpasses` in order;
  `y = (1 − mix)·x + mix·w`. Real samples; 1 to 64 combs, 0 to 64 all-passes, delays at least
  1, gains `|g| < 1`, `mix` in [0, 1]. **(implemented)**
- **Tape stop** (`tape_stop(samples, start, length)`, C# `Dsp.TapeStop`,
  [ADR 0296](adr/0296-tape-stop.md)): with `k = n − start` and `L = length`, the input for
  `k ≤ 0`; for `1 ≤ k < L`, `p = start + (k − k(k+1)/(2L))`, `i = ⌊p⌋`, `f = p − i`,
  `y = x[i]·(1 − f) + x[i+1]·f`; 0 for `k ≥ L`. Real, finite, non-empty samples; integer
  `start ≥ 0`, `length ≥ 1`. **(implemented)**
- **Damped feedback comb** (`lowpass_feedback_comb(samples, delay, feedback, damping)`, C#
  `Dsp.LowpassFeedbackComb`, [ADR 0297](adr/0297-lowpass-feedback-comb.md)):
  `f[n] = (1 − d)·y[n − D] + d·f[n − 1]`, `y[n] = x[n] + g·f[n]`, with `y[k < 0] = 0` and
  `f[−1] = 0`. Real, finite, non-empty samples; integer `delay ≥ 1`; `|feedback| < 1`;
  `damping` in [0, 1). **(implemented)**
- **Reverse delay** (`reverse_delay(samples, block, mix)`, C# `Dsp.ReverseDelay`,
  [ADR 0298](adr/0298-reverse-delay.md)): with `n = q·B + r`, `0 ≤ r < B`,
  `wet[n] = x[(q − 1)·B + (B − 1 − r)]` for `q ≥ 1` and 0 for `q = 0`;
  `y = (1 − mix)·x + mix·wet`. Real, finite, non-empty samples; integer `block ≥ 1`; `mix` in
  [0, 1]. **(implemented)**
- **Stutter** (`stutter(samples, start, length, repeats)`, C# `Dsp.Stutter`,
  [ADR 0299](adr/0299-stutter.md)): `y[n] = x[start + (n − start) mod length]` for
  `start ≤ n < start + repeats·length`, `x[n]` elsewhere. Real, finite, non-empty samples;
  integers `start ≥ 0`, `length ≥ 1`, `repeats ≥ 0`. **(implemented)**
- **Multi-tap delay** (`multitap_delay(samples, delays, gains)`, C# `Dsp.MultitapDelay`,
  [ADR 0300](adr/0300-multitap-delay.md)): `y[n] = x[n] + Σ_k g_k·x[n − d_k]`, `x[m < 0] = 0`,
  summed from `x[n]` with the taps in list order. Real, finite, non-empty samples; 1 to 64
  taps, integer delays at least 1, one finite gain each. **(implemented)**
- **Delay-line pitch shifter** (`pitch_shift(samples, ratio, window)`, C# `Dsp.PitchShift`,
  [ADR 0302](adr/0302-pitch-shift.md)): `t = (1 − ratio)·(n/W)`, `φ = t − floor(t)`,
  `φ_b = (φ + 1/2) − floor(φ + 1/2)`; taps read `n − W·φ` and `n − W·φ_b` with the vibrato's
  linear interpolation, `x[k] = 0` outside the signal; `y = sin²(πφ)·A + cos²(πφ)·B`. Real,
  finite, non-empty samples; finite `ratio > 0`; finite `window ≥ 1`. **(implemented)**
- **Karplus–Strong pluck** (`karplus_strong(excitation, delay, length, decay)`, C#
  `Dsp.KarplusStrong`, [ADR 0304](adr/0304-karplus-strong.md)): `e` zero-padded to `length`,
  `y[n] = e[n] + decay·((y[n − D] + y[n − D − 1])·0.5)`, `y[k < 0] = 0`. Real, finite
  excitation of 1 to `length` samples; integers `delay ≥ 1`, `length ≥ 1`; `decay` in [0, 1].
  **(implemented)**
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
- **Colored noise** (`color_noise(white, exponent)`, C# `Channel.ColorNoise`,
  [ADR 0318](adr/0318-color-noise.md)): `X = DFT(white)`; bin `k` scaled by
  `min(k, N − k)^(−exponent/2)`, bin 0 by 0; `y = Re(IDFT(·))`, circular, not normalized. Real,
  one-dimensional, finite `white` (may be empty); finite `exponent`: 1 pink, 2 brown, −1
  blue. **(implemented)**
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
- **Farrow variable delay** (`farrow_delay(samples, delays, *, order=3)`, C#
  `Channel.FarrowDelay`, [ADR 0226](adr/0226-farrow-delay.md)): for `n = 0 … L−1`,
  `p = n − delays[n]`, `q = p − (N−1)/2`, `b = ⌊q⌋`, `μ = q − b`,
  `y[n] = Σ_{j=0}^{N} L_j(μ + (N−1)/2) x[b+j]` with `L_j(u) = Π_{m≠j} (u − m)/(j − m)`, `N = order`,
  `x` zero outside `0 … L−1`. Computed in Farrow form: `L_j(μ + (N−1)/2) = Σ_k c[j][k] μ^k`, built
  by multiplying by `(μ + (N−1)/2 − m)/(j − m)` over increasing `m ≠ j`;
  `v_k = Σ_j c[j][k] x[b+j]` (increasing `j`); `y = v(μ)` by Horner from `v_N`. Output complex, as
  long as the input. `delays` as long as `samples`, finite (negative advances); integer
  `order ≥ 1`. Odd orders shift exactly at integer delays. **(implemented)**
- **Farrow resampler** (`farrow_resample(samples, ratio, *, order=3)`, C#
  `Channel.FarrowResample`, [ADR 0228](adr/0228-farrow-resample.md)): output `k` is the Farrow
  variable delay's interpolator read at `t_k = k / ratio` (one floating-point division) in place
  of `n − delays[n]`, for `k = 0, 1, …` while `t_k ≤ L − 1`. `ratio` = output rate / input rate,
  finite, within `[1e-6, 1e6]`; integer `order ≥ 1`. No anti-alias filtering. Output complex;
  empty input gives empty output. **(implemented)**
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
