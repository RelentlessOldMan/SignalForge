using System.Numerics;

namespace SignalForge;

public static partial class Dsp
{
    /// <summary>RMS of the <paramref name="length"/> real samples ending at each sample, zeros
    /// before the start (conventions: Moving RMS; ADR 0239).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="length">The window length <c>N</c>, at least 1.</param>
    /// <returns>One RMS value per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] MovingRms(ReadOnlySpan<double> samples, int length) =>
        MovingRms((ReadOnlySpan<Complex>)ToComplexArray(samples), length);

    /// <summary>RMS of the <paramref name="length"/> complex samples ending at each sample, zeros
    /// before the start (conventions: Moving RMS; ADR 0239).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="length">The window length <c>N</c>, at least 1.</param>
    /// <returns>One RMS value per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] MovingRms(ReadOnlySpan<Complex> samples, int length)
    {
        if (length < 1)
            throw new ArgumentOutOfRangeException(nameof(length), "length must be at least 1");
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        var sq = new double[samples.Length];
        for (int n = 0; n < samples.Length; n++)
        {
            Complex v = samples[n];
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
            double a = Complex.Abs(v);
            sq[n] = a * a;
        }
        var y = new double[samples.Length];
        for (int n = 0; n < samples.Length; n++)
        {
            double acc = 0;
            for (int k = Math.Max(0, n - length + 1); k <= n; k++)
                acc += sq[k];
            y[n] = Math.Sqrt(acc / length);
        }
        return y;
    }
}
