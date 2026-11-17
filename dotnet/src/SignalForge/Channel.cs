using System.Numerics;

namespace SignalForge;

/// <summary>Channel impairments. Definitions in docs/conventions.md (Channel).</summary>
public static class Channel
{
    /// <summary>
    /// Adds circular complex Gaussian noise of total variance P·sps / 10^(Es/N0 / 10), where P is
    /// <paramref name="signalPower"/> or, if null, the measured mean |x|².
    /// </summary>
    /// <param name="samples">Complex samples, at least one, all finite.</param>
    /// <param name="esN0Db">Es/N0 in dB, finite.</param>
    /// <param name="samplesPerSymbol">Samples per symbol, at least 1.</param>
    /// <param name="seed">Seed for the noise; the stream differs from the Python one.</param>
    /// <param name="signalPower">Reference power per sample, positive and finite; null to measure it.</param>
    public static Complex[] Awgn(ReadOnlySpan<Complex> samples, double esN0Db, int samplesPerSymbol, int seed,
        double? signalPower = null) =>
        Awgn(samples, esN0Db, samplesPerSymbol, new Random(seed), signalPower);

    /// <summary>As <see cref="Awgn(ReadOnlySpan{Complex}, double, int, int, double?)"/>, drawing from
    /// <paramref name="rng"/>.</summary>
    /// <param name="samples">Complex samples, at least one, all finite.</param>
    /// <param name="esN0Db">Es/N0 in dB, finite.</param>
    /// <param name="samplesPerSymbol">Samples per symbol, at least 1.</param>
    /// <param name="rng">Source of the noise.</param>
    /// <param name="signalPower">Reference power per sample, positive and finite; null to measure it.</param>
    public static Complex[] Awgn(ReadOnlySpan<Complex> samples, double esN0Db, int samplesPerSymbol, Random rng,
        double? signalPower = null)
    {
        ArgumentNullException.ThrowIfNull(rng);
        if (samples.IsEmpty)
            throw new ArgumentException("awgn needs at least one sample", nameof(samples));
        if (!double.IsFinite(esN0Db))
            throw new ArgumentOutOfRangeException(nameof(esN0Db), esN0Db, "must be finite");
        ArgumentOutOfRangeException.ThrowIfLessThan(samplesPerSymbol, 1);
        double sum = 0;
        foreach (var x in samples)
        {
            if (!double.IsFinite(x.Real) || !double.IsFinite(x.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
            sum += x.Real * x.Real + x.Imaginary * x.Imaginary;
        }
        double p = Check.PositiveFinite(signalPower ?? sum / samples.Length, nameof(signalPower));
        double variance = p * samplesPerSymbol * Math.Pow(10, -esN0Db / 10);
        if (!double.IsFinite(variance))
            throw new ArgumentOutOfRangeException(nameof(esN0Db), esN0Db, "so low that the noise variance overflows");
        double sigma = Math.Sqrt(variance / 2);
        var y = new Complex[samples.Length];
        for (int i = 0; i < y.Length; i++)
        {
            // Box–Muller: one pair of uniforms gives one complex Gaussian sample.
            double r = Math.Sqrt(-2 * Math.Log(1 - rng.NextDouble()));
            double phi = 2 * Math.PI * rng.NextDouble();
            y[i] = samples[i] + new Complex(sigma * r * Math.Cos(phi), sigma * r * Math.Sin(phi));
        }
        return y;
    }

    /// <summary>x[n]·e^{j(2π·Δf·n/fs + φ)}; a positive offset moves the spectrum up.</summary>
    /// <param name="samples">Complex samples.</param>
    /// <param name="offsetHz">Frequency offset in Hz, finite.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="phase">Starting phase in radians, finite.</param>
    public static Complex[] FrequencyOffset(ReadOnlySpan<Complex> samples, double offsetHz, double sampleRate,
        double phase = 0)
    {
        Check.PositiveFinite(sampleRate, nameof(sampleRate));
        if (!double.IsFinite(offsetHz))
            throw new ArgumentOutOfRangeException(nameof(offsetHz), offsetHz, "must be finite");
        if (!double.IsFinite(phase))
            throw new ArgumentOutOfRangeException(nameof(phase), phase, "must be finite");
        var y = new Complex[samples.Length];
        for (int n = 0; n < y.Length; n++)
            y[n] = samples[n] * Complex.FromPolarCoordinates(1, 2 * Math.PI * offsetHz * (n / sampleRate) + phase);
        return y;
    }

    /// <summary>Wiener phase noise: x[n]·e^{jφ[n]}, φ[0] = 0, Gaussian increments of variance
    /// 2π·linewidth/fs (conventions: Channel, Phase noise).</summary>
    /// <param name="samples">Complex samples.</param>
    /// <param name="linewidthHz">Full 3 dB width of the Lorentzian line in Hz, finite, not negative.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="seed">Seed for the phase walk; the stream differs from the Python one.</param>
    public static Complex[] PhaseNoise(ReadOnlySpan<Complex> samples, double linewidthHz, double sampleRate, int seed) =>
        PhaseNoise(samples, linewidthHz, sampleRate, new Random(seed));

    /// <summary>As <see cref="PhaseNoise(ReadOnlySpan{Complex}, double, double, int)"/>, drawing from
    /// <paramref name="rng"/>.</summary>
    /// <param name="samples">Complex samples.</param>
    /// <param name="linewidthHz">Full 3 dB width of the Lorentzian line in Hz, finite, not negative.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="rng">Source of the phase walk.</param>
    public static Complex[] PhaseNoise(ReadOnlySpan<Complex> samples, double linewidthHz, double sampleRate, Random rng)
    {
        ArgumentNullException.ThrowIfNull(rng);
        Check.PositiveFinite(sampleRate, nameof(sampleRate));
        if (!(linewidthHz >= 0 && double.IsFinite(linewidthHz)))
            throw new ArgumentOutOfRangeException(nameof(linewidthHz), linewidthHz, "must be finite and not negative");
        double sigma = Math.Sqrt(2 * Math.PI * linewidthHz / sampleRate);
        var y = new Complex[samples.Length];
        double phi = 0;
        for (int n = 0; n < y.Length; n++)
        {
            if (n > 0)
            {
                // Box–Muller, the cosine branch: one pair of uniforms gives one Gaussian step.
                double r = Math.Sqrt(-2 * Math.Log(1 - rng.NextDouble()));
                phi += sigma * r * Math.Cos(2 * Math.PI * rng.NextDouble());
            }
            y[n] = samples[n] * Complex.FromPolarCoordinates(1, phi);
        }
        return y;
    }

    /// <summary>I + j·g·(Q·cos φ + I·sin φ), g = 10^(gainDb/20): the error on the Q branch
    /// (conventions: Channel, IQ imbalance).</summary>
    /// <param name="samples">Complex samples.</param>
    /// <param name="gainDb">Q-branch gain relative to I in dB, finite.</param>
    /// <param name="phase">Q-branch phase error in radians, finite; positive advances Q.</param>
    public static Complex[] IqImbalance(ReadOnlySpan<Complex> samples, double gainDb, double phase)
    {
        double g = ImbalanceGain(gainDb, phase);
        double c = g * Math.Cos(phase), s = g * Math.Sin(phase);
        var y = new Complex[samples.Length];
        for (int n = 0; n < y.Length; n++)
            y[n] = new Complex(samples[n].Real, samples[n].Imaginary * c + samples[n].Real * s);
        return y;
    }

    /// <summary>Tone-to-image power ratio in dB of <see cref="IqImbalance"/> with these arguments;
    /// +∞ with no imbalance (conventions: Channel, Image rejection).</summary>
    /// <param name="gainDb">Q-branch gain relative to I in dB, finite.</param>
    /// <param name="phase">Q-branch phase error in radians, finite.</param>
    public static double IqImageRejectionDb(double gainDb, double phase)
    {
        double g = ImbalanceGain(gainDb, phase);
        double num = 1 + g * g + 2 * g * Math.Cos(phase);
        double den = 1 + g * g - 2 * g * Math.Cos(phase);
        return den <= 0 ? double.PositiveInfinity : 10 * Math.Log10(num / den);
    }

    /// <summary>Saleh's travelling-wave tube model, A(r) = αa·r/(1 + βa·r²) and
    /// Φ(r) = αφ·r²/(1 + βφ·r²), on the complex envelope (conventions: Channel, Amplifier models; ADR 0114).</summary>
    /// <param name="samples">Complex envelope samples.</param>
    /// <param name="alphaA">Small-signal gain αa, positive and finite.</param>
    /// <param name="betaA">AM/AM knee βa, finite and not negative.</param>
    /// <param name="alphaPhi">AM/PM scale αφ in radians, finite.</param>
    /// <param name="betaPhi">AM/PM knee βφ, finite and not negative.</param>
    /// <exception cref="ArgumentOutOfRangeException">A parameter is out of range.</exception>
    public static Complex[] SalehAmplifier(ReadOnlySpan<Complex> samples, double alphaA, double betaA, double alphaPhi, double betaPhi)
    {
        Check.PositiveFinite(alphaA, nameof(alphaA));
        Check.Finite(alphaPhi, nameof(alphaPhi));
        if (!(betaA >= 0) || !double.IsFinite(betaA))
            throw new ArgumentOutOfRangeException(nameof(betaA), betaA, "must be finite and not negative");
        if (!(betaPhi >= 0) || !double.IsFinite(betaPhi))
            throw new ArgumentOutOfRangeException(nameof(betaPhi), betaPhi, "must be finite and not negative");
        var y = new Complex[samples.Length];
        for (int n = 0; n < y.Length; n++)
        {
            double r = Complex.Abs(samples[n]);
            double r2 = r * r;
            double phi = alphaPhi * r2 / (1 + betaPhi * r2);
            y[n] = samples[n] * (alphaA / (1 + betaA * r2)) * new Complex(Math.Cos(phi), Math.Sin(phi));
        }
        return y;
    }

    /// <summary>Rapp's solid-state model, A(r) = g·r/(1 + (g·r/Asat)^(2p))^(1/(2p)) with no phase shift,
    /// on the complex envelope (conventions: Channel, Amplifier models; ADR 0114).</summary>
    /// <param name="samples">Complex envelope samples.</param>
    /// <param name="gain">Small-signal gain g, positive and finite.</param>
    /// <param name="saturation">Saturated output amplitude Asat, positive and finite.</param>
    /// <param name="smoothness">Knee smoothness p, positive and finite.</param>
    /// <exception cref="ArgumentOutOfRangeException">A parameter is out of range.</exception>
    public static Complex[] RappAmplifier(ReadOnlySpan<Complex> samples, double gain, double saturation, double smoothness)
    {
        Check.PositiveFinite(gain, nameof(gain));
        Check.PositiveFinite(saturation, nameof(saturation));
        Check.PositiveFinite(smoothness, nameof(smoothness));
        var y = new Complex[samples.Length];
        for (int n = 0; n < y.Length; n++)
        {
            double r = Complex.Abs(samples[n]);
            double u = gain * r / saturation;
            y[n] = u <= 1
                ? samples[n] * (gain / Math.Pow(1 + Math.Pow(u, 2 * smoothness), 1 / (2 * smoothness)))
                : samples[n] / r * (saturation / Math.Pow(1 + Math.Pow(u, -2 * smoothness), 1 / (2 * smoothness)));
        }
        return y;
    }

    /// <summary>samples + offset (conventions: Channel, DC offset).</summary>
    /// <param name="samples">Complex samples.</param>
    /// <param name="offset">The constant added, finite in both parts.</param>
    public static Complex[] DcOffset(ReadOnlySpan<Complex> samples, Complex offset)
    {
        if (!double.IsFinite(offset.Real) || !double.IsFinite(offset.Imaginary))
            throw new ArgumentOutOfRangeException(nameof(offset), offset, "must be finite");
        var y = new Complex[samples.Length];
        for (int n = 0; n < y.Length; n++)
            y[n] = samples[n] + offset;
        return y;
    }

    /// <summary>Static tapped delay line: y[n] = Σᵢ gains[i]·x[n − delays[i]], as long as the input
    /// (conventions: Channel, Multipath).</summary>
    /// <param name="samples">Complex samples.</param>
    /// <param name="delays">Path delays in samples, each not negative.</param>
    /// <param name="gains">Path gains, finite, as many as <paramref name="delays"/>.</param>
    public static Complex[] Multipath(ReadOnlySpan<Complex> samples, ReadOnlySpan<int> delays, ReadOnlySpan<Complex> gains)
    {
        if (delays.Length == 0 || delays.Length != gains.Length)
            throw new ArgumentException("delays and gains must have equal non-zero length", nameof(gains));
        for (int i = 0; i < delays.Length; i++)
        {
            if (delays[i] < 0)
                throw new ArgumentOutOfRangeException(nameof(delays), delays[i], "must not be negative");
            if (!double.IsFinite(gains[i].Real) || !double.IsFinite(gains[i].Imaginary))
                throw new ArgumentOutOfRangeException(nameof(gains), gains[i], "must be finite");
        }
        var y = new Complex[samples.Length];
        for (int i = 0; i < delays.Length; i++)
            for (int n = delays[i]; n < y.Length; n++)
                y[n] += gains[i] * samples[n - delays[i]];
        return y;
    }

    /// <summary>Flat block fading: each block of <paramref name="blockLength"/> samples times one
    /// Rician gain of unit mean power, K = 0 for Rayleigh (conventions: Channel, Block fading).</summary>
    /// <param name="samples">Complex samples.</param>
    /// <param name="kFactor">Rician K factor, not negative; infinity means no fading.</param>
    /// <param name="blockLength">Samples per gain, at least 1; the last block may be short.</param>
    /// <param name="seed">Seed for the gains.</param>
    public static Complex[] RicianFading(ReadOnlySpan<Complex> samples, double kFactor, int blockLength, int seed) =>
        RicianFading(samples, kFactor, blockLength, new Random(seed));

    /// <summary>As <see cref="RicianFading(ReadOnlySpan{Complex}, double, int, int)"/>, drawing from
    /// <paramref name="rng"/>.</summary>
    /// <param name="samples">Complex samples.</param>
    /// <param name="kFactor">Rician K factor, not negative; infinity means no fading.</param>
    /// <param name="blockLength">Samples per gain, at least 1; the last block may be short.</param>
    /// <param name="rng">Source of the gains.</param>
    public static Complex[] RicianFading(ReadOnlySpan<Complex> samples, double kFactor, int blockLength, Random rng)
    {
        ArgumentNullException.ThrowIfNull(rng);
        if (!(kFactor >= 0))
            throw new ArgumentOutOfRangeException(nameof(kFactor), kFactor, "must not be negative or NaN");
        ArgumentOutOfRangeException.ThrowIfLessThan(blockLength, 1);
        if (double.IsPositiveInfinity(kFactor))
            return samples.ToArray();
        double los = Math.Sqrt(kFactor / (kFactor + 1)), spread = Math.Sqrt(1 / (kFactor + 1) / 2);
        var y = new Complex[samples.Length];
        Complex g = Complex.Zero;
        for (int n = 0; n < y.Length; n++)
        {
            if (n % blockLength == 0)
            {
                double a = Gaussian(rng), b = Gaussian(rng);
                g = new Complex(los + spread * a, spread * b);
            }
            y[n] = g * samples[n];
        }
        return y;
    }

    // Box–Muller, the cosine branch: one pair of uniforms gives one standard Gaussian.
    private static double Gaussian(Random rng) =>
        Math.Sqrt(-2 * Math.Log(1 - rng.NextDouble())) * Math.Cos(2 * Math.PI * rng.NextDouble());

    private const double FractionalDelayBeta = 8;

    /// <summary>Delay by <paramref name="delay"/> samples through a Kaiser-windowed sinc of
    /// 2·<paramref name="halfWidth"/> taps, as long as the input (conventions: Channel, Fractional
    /// delay).</summary>
    /// <param name="samples">Complex samples.</param>
    /// <param name="delay">Delay in samples, finite; negative advances.</param>
    /// <param name="halfWidth">Half the interpolator's length in samples, at least 1.</param>
    public static Complex[] FractionalDelay(ReadOnlySpan<Complex> samples, double delay, int halfWidth = 16)
    {
        if (!double.IsFinite(delay))
            throw new ArgumentOutOfRangeException(nameof(delay), delay, "must be finite");
        ArgumentOutOfRangeException.ThrowIfLessThan(halfWidth, 1);
        double norm = Spectral.BesselI0(FractionalDelayBeta);
        int n = samples.Length;
        var y = new Complex[n];
        // the kernel depends on the sample only through its fraction, which takes few distinct
        // values: evaluate it once per fraction (the same arithmetic) and reuse it
        var kernels = new Dictionary<double, double[]>();
        for (int i = 0; i < n; i++)
        {
            double pos = i - delay, b = Math.Floor(pos), f = pos - b;
            if (!kernels.TryGetValue(f, out double[]? taps))
            {
                taps = DelayKernel(f, halfWidth, norm);
                kernels[f] = taps;
            }
            for (int j = -halfWidth + 1; j <= halfWidth; j++)
            {
                double m = b + j;
                if (m >= 0 && m < n)
                    y[i] += taps[j + halfWidth - 1] * samples[(int)m];
            }
        }
        return y;
    }

    /// <summary>Delay each sample by its own <c>delays[n]</c> through the order-<paramref name="order"/>
    /// Lagrange interpolator in Farrow form, as long as the input (conventions: Channel, Farrow
    /// variable delay; ADR 0226).</summary>
    /// <param name="samples">Complex samples.</param>
    /// <param name="delays">One delay per sample, in samples, finite; negative advances.</param>
    /// <param name="order">The interpolation order, at least 1; odd orders shift exactly at integer
    /// delays.</param>
    /// <returns><c>y[n]</c>, the input read at <c>n − delays[n]</c>, zero outside the input.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] FarrowDelay(ReadOnlySpan<Complex> samples, ReadOnlySpan<double> delays, int order = 3)
    {
        if (delays.Length != samples.Length)
            throw new ArgumentException("delays must be as long as samples", nameof(delays));
        foreach (double d in delays)
        {
            if (!double.IsFinite(d))
                throw new ArgumentOutOfRangeException(nameof(delays), d, "must be finite");
        }
        ArgumentOutOfRangeException.ThrowIfLessThan(order, 1);
        int len = samples.Length;
        double half = (order - 1) / 2.0;
        var c = new double[order + 1][];
        for (int j = 0; j <= order; j++)
        {
            double[] poly = [1.0];
            for (int m = 0; m <= order; m++)
            {
                if (m == j)
                    continue;
                double s = half - m, g = j - m;
                var next = new double[poly.Length + 1];
                for (int k = 0; k < poly.Length; k++)
                {
                    next[k] += poly[k] * s / g;
                    next[k + 1] += poly[k] / g;
                }
                poly = next;
            }
            c[j] = poly;
        }
        var y = new Complex[len];
        var v = new Complex[order + 1];
        for (int i = 0; i < len; i++)
        {
            double q = i - delays[i] - half, b = Math.Floor(q), mu = q - b;
            Array.Clear(v);
            for (int j = 0; j <= order; j++)
            {
                double m = b + j;
                Complex xj = m >= 0 && m < len ? samples[(int)m] : Complex.Zero;
                for (int k = 0; k <= order; k++)
                    v[k] += c[j][k] * xj;
            }
            Complex acc = v[order];
            for (int k = order - 1; k >= 0; k--)
                acc = acc * mu + v[k];
            y[i] = acc;
        }
        return y;
    }

    /// <summary>The input read every 1 + ppm/1e6 samples through the fractional-delay kernel: a
    /// receiver whose sample clock is off by <paramref name="ppm"/> (conventions: Channel, Sample
    /// clock offset).</summary>
    /// <param name="samples">Complex samples.</param>
    /// <param name="ppm">Clock offset in parts per million, finite, within ±1e5; positive spreads
    /// the samples further apart.</param>
    /// <param name="halfWidth">Half the interpolator's length in samples, at least 1.</param>
    public static Complex[] ClockOffset(ReadOnlySpan<Complex> samples, double ppm, int halfWidth = 16)
    {
        if (!(Math.Abs(ppm) <= 1e5))
            throw new ArgumentOutOfRangeException(nameof(ppm), ppm, "must be finite and within 1e5");
        ArgumentOutOfRangeException.ThrowIfLessThan(halfWidth, 1);
        double r = 1 + ppm / 1e6;
        var y = new List<Complex>();
        for (int n = 0; n * r <= samples.Length - 1; n++)
            y.Add(Interpolate(samples, n * r, halfWidth));
        return [.. y];
    }

    /// <summary>The input read by a receiver whose clock offset moves linearly from
    /// <paramref name="ppmStart"/> at the first input sample to <paramref name="ppmEnd"/> at the
    /// last (conventions: Channel, Sample clock drift; ADR 0102).</summary>
    /// <param name="samples">Complex samples.</param>
    /// <param name="ppmStart">Clock offset at the first input sample in parts per million, finite,
    /// within ±1e5; positive spreads the samples further apart.</param>
    /// <param name="ppmEnd">Clock offset at the last input sample, as <paramref name="ppmStart"/>.</param>
    /// <param name="halfWidth">Half the interpolator's length in samples, at least 1.</param>
    /// <returns>The samples read at each position up to the last input sample.</returns>
    /// <exception cref="ArgumentOutOfRangeException">An argument is out of range.</exception>
    public static Complex[] ClockDrift(ReadOnlySpan<Complex> samples, double ppmStart, double ppmEnd, int halfWidth = 16)
    {
        if (!(Math.Abs(ppmStart) <= 1e5))
            throw new ArgumentOutOfRangeException(nameof(ppmStart), ppmStart, "must be finite and within 1e5");
        if (!(Math.Abs(ppmEnd) <= 1e5))
            throw new ArgumentOutOfRangeException(nameof(ppmEnd), ppmEnd, "must be finite and within 1e5");
        ArgumentOutOfRangeException.ThrowIfLessThan(halfWidth, 1);
        int last = samples.Length - 1;
        double r = 1 + ppmStart / 1e6;
        double d = last > 0 ? (ppmEnd - ppmStart) / 1e6 / last : 0;
        double g = Spectral.LogP1(d);
        var y = new List<Complex>();
        for (int n = 0; ; n++)
        {
            double t = d == 0 ? n * r : r * Spectral.ExpM1(n * g) / d;
            if (!(t <= last))
                break;
            y.Add(Interpolate(samples, t, halfWidth));
        }
        return [.. y];
    }

    /// <summary>The input read at n + rms·gₙ, gₙ independent standard Gaussians, through the
    /// fractional-delay kernel: white sampling jitter (conventions: Channel, Sample clock jitter;
    /// ADR 0104).</summary>
    /// <param name="samples">Complex samples.</param>
    /// <param name="rms">The jitter's standard deviation in samples, finite, from 0 to 0.5.</param>
    /// <param name="seed">Seed for the jitter; the stream differs from the Python one.</param>
    /// <param name="halfWidth">Half the interpolator's length in samples, at least 1.</param>
    /// <returns>One sample per input sample.</returns>
    /// <exception cref="ArgumentOutOfRangeException">An argument is out of range.</exception>
    public static Complex[] ClockJitter(ReadOnlySpan<Complex> samples, double rms, int seed, int halfWidth = 16) =>
        ClockJitter(samples, rms, new Random(seed), halfWidth);

    /// <summary>As <see cref="ClockJitter(ReadOnlySpan{Complex}, double, int, int)"/>, drawing from
    /// <paramref name="rng"/>.</summary>
    /// <param name="samples">Complex samples.</param>
    /// <param name="rms">The jitter's standard deviation in samples, finite, from 0 to 0.5.</param>
    /// <param name="rng">Source of the jitter.</param>
    /// <param name="halfWidth">Half the interpolator's length in samples, at least 1.</param>
    /// <returns>One sample per input sample.</returns>
    /// <exception cref="ArgumentOutOfRangeException">An argument is out of range.</exception>
    public static Complex[] ClockJitter(ReadOnlySpan<Complex> samples, double rms, Random rng, int halfWidth = 16)
    {
        ArgumentNullException.ThrowIfNull(rng);
        if (!(rms >= 0 && rms <= 0.5))
            throw new ArgumentOutOfRangeException(nameof(rms), rms, "must be between 0 and 0.5 samples");
        ArgumentOutOfRangeException.ThrowIfLessThan(halfWidth, 1);
        var y = new Complex[samples.Length];
        for (int n = 0; n < y.Length; n++)
        {
            // Box–Muller, the cosine branch: one pair of uniforms gives one Gaussian.
            double r = Math.Sqrt(-2 * Math.Log(1 - rng.NextDouble()));
            double g = r * Math.Cos(2 * Math.PI * rng.NextDouble());
            y[n] = Interpolate(samples, n + rms * g, halfWidth);
        }
        return y;
    }

    // h(f − j) for j = −H+1 … H (conventions: Channel, Fractional delay).
    private static double[] DelayKernel(double f, int halfWidth, double norm)
    {
        var taps = new double[2 * halfWidth];
        for (int j = -halfWidth + 1; j <= halfWidth; j++)
        {
            double t = f - j;
            if (Math.Abs(t) >= halfWidth)
                continue;
            double s = t == 0 ? 1 : f == 0 ? 0 : Math.Sin(Math.PI * t) / (Math.PI * t);
            double u = t / halfWidth;
            taps[j + halfWidth - 1] = s * (Spectral.BesselI0(FractionalDelayBeta * Math.Sqrt(Math.Max(1 - u * u, 0))) / norm);
        }
        return taps;
    }

    /// <summary>z(t) through the fractional-delay kernel (conventions: Synchronization, Tracking
    /// loops); the same arithmetic as <see cref="FractionalDelay"/>.</summary>
    internal static Complex Interpolate(ReadOnlySpan<Complex> y, double t, int halfWidth)
    {
        double b = Math.Floor(t);
        double[] taps = DelayKernel(t - b, halfWidth, Spectral.BesselI0(FractionalDelayBeta));
        Complex acc = Complex.Zero;
        for (int j = -halfWidth + 1; j <= halfWidth; j++)
        {
            double m = b + j;
            if (m >= 0 && m < y.Length)
                acc += taps[j + halfWidth - 1] * y[(int)m];
        }
        return acc;
    }

    private static double ImbalanceGain(double gainDb, double phase)
    {
        if (!double.IsFinite(gainDb))
            throw new ArgumentOutOfRangeException(nameof(gainDb), gainDb, "must be finite");
        if (!double.IsFinite(phase))
            throw new ArgumentOutOfRangeException(nameof(phase), phase, "must be finite");
        double g = Math.Pow(10, gainDb / 20);
        if (!(g > 0 && double.IsFinite(g)))
            throw new ArgumentOutOfRangeException(nameof(gainDb), gainDb, "gain out of range");
        return g;
    }
}
