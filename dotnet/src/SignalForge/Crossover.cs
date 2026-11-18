namespace SignalForge;

/// <summary>The low and high bands of a crossover, each a cascade of second-order sections
/// <c>[b0, b1, b2, a0, a1, a2]</c> (conventions: Linkwitz-Riley crossover; ADR 0284).</summary>
/// <param name="Low">The low band's sections.</param>
/// <param name="High">The high band's sections.</param>
public sealed record Crossover(double[][] Low, double[][] High);

/// <summary>The low and high bands of a split signal (conventions: Two-band splitter;
/// ADR 0285).</summary>
/// <param name="Low">The low band.</param>
/// <param name="High">The high band.</param>
public sealed record Bands(double[] Low, double[] High);

public static partial class Dsp
{
    /// <summary>Linkwitz-Riley crossover of even <paramref name="order"/>: each band a squared
    /// Butterworth of half the order, the two summing to an all-pass (conventions: Linkwitz-Riley
    /// crossover; ADR 0284).</summary>
    /// <param name="order">The crossover order, even, from 2 to 2000.</param>
    /// <param name="cutoff">The crossover frequency, Hz, between 0 and sampleRate/2.</param>
    /// <param name="sampleRate">The sample rate, Hz.</param>
    /// <returns>The low and high bands.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Crossover LinkwitzRiley(int order, double cutoff, double sampleRate)
    {
        if (order < 2 || order > 2000 || order % 2 != 0)
            throw new ArgumentOutOfRangeException(nameof(order), "order must be even, from 2 to 2000");
        double[][] lo = ButterworthLowpass(order / 2, cutoff, sampleRate);
        double[][] hi = ButterworthHighpass(order / 2, cutoff, sampleRate);
        double[][] low = [.. lo.Select(r => (double[])r.Clone()), .. lo.Select(r => (double[])r.Clone())];
        double[][] high = [.. hi.Select(r => (double[])r.Clone()), .. hi.Select(r => (double[])r.Clone())];
        if (order / 2 % 2 == 1)
        {
            for (int i = 0; i < 3; i++)
                high[0][i] = -high[0][i];
        }
        return new Crossover(low, high);
    }

    /// <summary>Splits real samples into the low and high bands of a Linkwitz-Riley crossover,
    /// each run from rest (conventions: Two-band splitter; ADR 0285).</summary>
    /// <param name="samples">Real, finite samples, at least one.</param>
    /// <param name="order">The crossover order, even, from 2 to 2000.</param>
    /// <param name="cutoff">The crossover frequency, Hz, between 0 and sampleRate/2.</param>
    /// <param name="sampleRate">The sample rate, Hz.</param>
    /// <returns>The low and high bands, each as long as the input.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Bands CrossoverSplit(ReadOnlySpan<double> samples, int order, double cutoff, double sampleRate)
    {
        Crossover lr = LinkwitzRiley(order, cutoff, sampleRate);
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        return new Bands(new IirFilter(lr.Low).Process(samples), new IirFilter(lr.High).Process(samples));
    }

    /// <summary>Splits real samples with a Linkwitz-Riley crossover, compresses each band with
    /// its own threshold and ratio, and sums them (conventions: Two-band compressor;
    /// ADR 0287).</summary>
    /// <param name="samples">Real, finite samples, at least one.</param>
    /// <param name="order">The crossover order, even, from 2 to 2000.</param>
    /// <param name="cutoff">The crossover frequency, Hz, between 0 and sampleRate/2.</param>
    /// <param name="sampleRate">The sample rate, Hz.</param>
    /// <param name="lowThresholdDb">The low band's threshold, dB.</param>
    /// <param name="lowRatio">The low band's ratio, at least 1.</param>
    /// <param name="highThresholdDb">The high band's threshold, dB.</param>
    /// <param name="highRatio">The high band's ratio, at least 1.</param>
    /// <param name="attack">The envelope followers' attack coefficient, in [0, 1).</param>
    /// <param name="release">The envelope followers' release coefficient, in [0, 1).</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] TwoBandCompress(ReadOnlySpan<double> samples, int order, double cutoff, double sampleRate, double lowThresholdDb, double lowRatio, double highThresholdDb, double highRatio, double attack, double release)
    {
        Bands b = CrossoverSplit(samples, order, cutoff, sampleRate);
        double[] lo = Compress(b.Low, lowThresholdDb, lowRatio, attack, release);
        double[] hi = Compress(b.High, highThresholdDb, highRatio, attack, release);
        for (int n = 0; n < lo.Length; n++)
            lo[n] += hi[n];
        return lo;
    }

    /// <summary>Adds soft-clipped harmonics of the band above <paramref name="cutoff"/> to real
    /// samples (conventions: Harmonic exciter; ADR 0288).</summary>
    /// <param name="samples">Real, finite samples, at least one.</param>
    /// <param name="order">The crossover order, even, from 2 to 2000.</param>
    /// <param name="cutoff">The crossover frequency, Hz, between 0 and sampleRate/2.</param>
    /// <param name="sampleRate">The sample rate, Hz.</param>
    /// <param name="drive">The gain into the clipper, finite and positive.</param>
    /// <param name="mix">The amount of the clipped band added, in [0, 1].</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] Exciter(ReadOnlySpan<double> samples, int order, double cutoff, double sampleRate, double drive, double mix)
    {
        if (!(drive > 0 && double.IsFinite(drive)))
            throw new ArgumentOutOfRangeException(nameof(drive), "drive must be finite and positive");
        CheckMix(mix);
        Bands b = CrossoverSplit(samples, order, cutoff, sampleRate);
        double[] u = new double[b.High.Length];
        for (int n = 0; n < u.Length; n++)
            u[n] = drive * b.High[n];
        double[] c = SoftClip(u);
        double[] y = new double[u.Length];
        for (int n = 0; n < y.Length; n++)
            y[n] = samples[n] + mix * (c[n] / drive);
        return y;
    }

    /// <summary>Adds the harmonics that soft clipping the band below <paramref name="cutoff"/>
    /// makes above it (conventions: Bass enhancer; ADR 0290).</summary>
    /// <param name="samples">Real, finite samples, at least one.</param>
    /// <param name="order">The crossover order, even, from 2 to 2000.</param>
    /// <param name="cutoff">The crossover frequency, Hz, between 0 and sampleRate/2.</param>
    /// <param name="sampleRate">The sample rate, Hz.</param>
    /// <param name="drive">The gain into the clipper, finite and positive.</param>
    /// <param name="mix">The amount of the harmonics added, in [0, 1].</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] BassEnhancer(ReadOnlySpan<double> samples, int order, double cutoff, double sampleRate, double drive, double mix)
    {
        if (!(drive > 0 && double.IsFinite(drive)))
            throw new ArgumentOutOfRangeException(nameof(drive), "drive must be finite and positive");
        CheckMix(mix);
        Bands b = CrossoverSplit(samples, order, cutoff, sampleRate);
        double[] u = new double[b.Low.Length];
        for (int n = 0; n < u.Length; n++)
            u[n] = drive * b.Low[n];
        double[] c = SoftClip(u);
        for (int n = 0; n < c.Length; n++)
            c[n] /= drive;
        double[] h = CrossoverSplit(c, order, cutoff, sampleRate).High;
        double[] y = new double[h.Length];
        for (int n = 0; n < y.Length; n++)
            y[n] = samples[n] + mix * h[n];
        return y;
    }
}
