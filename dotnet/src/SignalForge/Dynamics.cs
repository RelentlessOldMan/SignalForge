using System.Numerics;

namespace SignalForge;

public static partial class Dsp
{
    /// <summary>Static compressor gain in dB: 0 below the threshold, slope
    /// <c>1/ratio − 1</c> above, with a quadratic knee of width <paramref name="kneeDb"/>
    /// (conventions: Compressor gain computer; ADR 0254).</summary>
    /// <param name="levelDb">Finite input levels in dB, at least one.</param>
    /// <param name="thresholdDb">The threshold in dB, finite.</param>
    /// <param name="ratio">The compression ratio, finite and at least 1.</param>
    /// <param name="kneeDb">The knee width in dB, finite and at least 0.</param>
    /// <returns>One gain in dB, at most 0, per level.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] CompressorGain(ReadOnlySpan<double> levelDb, double thresholdDb, double ratio, double kneeDb = 0)
    {
        if (!double.IsFinite(thresholdDb))
            throw new ArgumentOutOfRangeException(nameof(thresholdDb), "threshold_db must be finite");
        if (!double.IsFinite(ratio) || !(ratio >= 1))
            throw new ArgumentOutOfRangeException(nameof(ratio), "ratio must be at least 1");
        if (!double.IsFinite(kneeDb) || !(kneeDb >= 0))
            throw new ArgumentOutOfRangeException(nameof(kneeDb), "knee_db must be at least 0");
        if (levelDb.IsEmpty)
            throw new ArgumentException("level_db must not be empty", nameof(levelDb));
        double s = 1 / ratio - 1;
        var g = new double[levelDb.Length];
        for (int n = 0; n < levelDb.Length; n++)
        {
            if (!double.IsFinite(levelDb[n]))
                throw new ArgumentException("level_db must be finite", nameof(levelDb));
            double d = levelDb[n] - thresholdDb;
            if (2 * d < -kneeDb)
                g[n] = 0;
            else if (2 * d > kneeDb)
                g[n] = s * d;
            else if (kneeDb > 0)
            {
                double q = d + kneeDb / 2;
                g[n] = s * q * q / (2 * kneeDb);
            }
        }
        return g;
    }

    /// <summary>Passes real samples while <c>|x| &gt; threshold</c> and for
    /// <paramref name="hold"/> samples after, 0 otherwise (conventions: Noise gate;
    /// ADR 0255).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="threshold">The opening level, finite and at least 0.</param>
    /// <param name="hold">Samples to stay open after the last one above the threshold, at least 0.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] NoiseGate(ReadOnlySpan<double> samples, double threshold, int hold = 0)
    {
        CheckNoiseGate(threshold, hold);
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        var y = new double[samples.Length];
        long c = (long)hold + 1;
        for (int n = 0; n < samples.Length; n++)
        {
            double v = samples[n];
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            c = Math.Abs(v) > threshold ? 0 : Math.Min(c + 1, (long)hold + 1);
            y[n] = c <= hold ? v : 0;
        }
        return y;
    }

    /// <summary>Passes complex samples while <c>|x| &gt; threshold</c> and for
    /// <paramref name="hold"/> samples after, 0 otherwise (conventions: Noise gate;
    /// ADR 0255).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="threshold">The opening level, finite and at least 0.</param>
    /// <param name="hold">Samples to stay open after the last one above the threshold, at least 0.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] NoiseGate(ReadOnlySpan<Complex> samples, double threshold, int hold = 0)
    {
        CheckNoiseGate(threshold, hold);
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        var y = new Complex[samples.Length];
        long c = (long)hold + 1;
        for (int n = 0; n < samples.Length; n++)
        {
            Complex v = samples[n];
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
            c = Complex.Abs(v) > threshold ? 0 : Math.Min(c + 1, (long)hold + 1);
            y[n] = c <= hold ? v : Complex.Zero;
        }
        return y;
    }

    private static void CheckNoiseGate(double threshold, int hold)
    {
        if (!double.IsFinite(threshold) || !(threshold >= 0))
            throw new ArgumentOutOfRangeException(nameof(threshold), "threshold must be at least 0");
        if (hold < 0)
            throw new ArgumentOutOfRangeException(nameof(hold), "hold must be at least 0");
    }
}
