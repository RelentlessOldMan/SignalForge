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
