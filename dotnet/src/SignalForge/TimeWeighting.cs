using System.Numerics;

namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The exponential time weighting <c>y[n] = α·y[n−1] + (1 − α)·|x[n]|²</c>,
    /// <c>α = exp(−1/(τ·fs))</c>, from 0 (conventions: Time weighting; ADR 0166).</summary>
    /// <param name="samples">Complex samples, finite; may be empty.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <param name="timeConstant">The time constant <c>τ</c> in seconds, finite and positive.</param>
    /// <returns>One power value per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] TimeWeighting(ReadOnlySpan<Complex> samples, double sampleRate, double timeConstant)
    {
        var p = new double[samples.Length];
        for (int n = 0; n < samples.Length; n++)
        {
            if (!(double.IsFinite(samples[n].Real) && double.IsFinite(samples[n].Imaginary)))
                throw new ArgumentException("samples must be finite", nameof(samples));
            p[n] = samples[n].Real * samples[n].Real + samples[n].Imaginary * samples[n].Imaginary;
        }
        return TimeWeightPowers(p, sampleRate, timeConstant);
    }

    /// <summary>The exponential time weighting <c>y[n] = α·y[n−1] + (1 − α)·x[n]²</c>,
    /// <c>α = exp(−1/(τ·fs))</c>, from 0 (conventions: Time weighting; ADR 0166).</summary>
    /// <param name="samples">Real samples, finite; may be empty.</param>
    /// <param name="sampleRate">Sample rate in Hz, finite and positive.</param>
    /// <param name="timeConstant">The time constant <c>τ</c> in seconds, finite and positive.</param>
    /// <returns>One power value per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] TimeWeighting(ReadOnlySpan<double> samples, double sampleRate, double timeConstant)
    {
        var p = new double[samples.Length];
        for (int n = 0; n < samples.Length; n++)
        {
            if (!double.IsFinite(samples[n]))
                throw new ArgumentException("samples must be finite", nameof(samples));
            p[n] = samples[n] * samples[n];
        }
        return TimeWeightPowers(p, sampleRate, timeConstant);
    }

    private static double[] TimeWeightPowers(double[] p, double sampleRate, double timeConstant)
    {
        if (!(double.IsFinite(sampleRate) && sampleRate > 0))
            throw new ArgumentOutOfRangeException(nameof(sampleRate), sampleRate, "must be finite and positive");
        if (!(double.IsFinite(timeConstant) && timeConstant > 0))
            throw new ArgumentOutOfRangeException(nameof(timeConstant), timeConstant, "must be finite and positive");
        double gain = -double.ExpM1(-1.0 / (timeConstant * sampleRate));
        double alpha = 1.0 - gain, y = 0;
        var output = new double[p.Length];
        for (int n = 0; n < p.Length; n++)
            output[n] = y = alpha * y + gain * p[n];
        return output;
    }
}
