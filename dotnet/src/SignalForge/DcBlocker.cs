using System.Numerics;

namespace SignalForge;

public static partial class Dsp
{
    /// <summary>The one-pole, one-zero DC blocker <c>y[n] = (x[n] − x[n−1]) + p·y[n−1]</c> from
    /// rest, for real samples (conventions: DC blocker; ADR 0236).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="pole">The pole <c>p</c>, in <c>[0, 1)</c>.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] DcBlocker(ReadOnlySpan<double> samples, double pole)
    {
        CheckDcBlocker(pole);
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        var y = new double[samples.Length];
        double xp = 0, yp = 0;
        for (int n = 0; n < samples.Length; n++)
        {
            yp = (samples[n] - xp) + pole * yp;
            xp = samples[n];
            y[n] = yp;
        }
        return y;
    }

    /// <summary>The one-pole, one-zero DC blocker <c>y[n] = (x[n] − x[n−1]) + p·y[n−1]</c> from
    /// rest, for complex samples (conventions: DC blocker; ADR 0236).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="pole">The pole <c>p</c>, in <c>[0, 1)</c>.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] DcBlocker(ReadOnlySpan<Complex> samples, double pole)
    {
        CheckDcBlocker(pole);
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (Complex v in samples)
        {
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        var y = new Complex[samples.Length];
        Complex xp = Complex.Zero, yp = Complex.Zero;
        for (int n = 0; n < samples.Length; n++)
        {
            yp = (samples[n] - xp) + pole * yp;
            xp = samples[n];
            y[n] = yp;
        }
        return y;
    }

    private static void CheckDcBlocker(double pole)
    {
        if (!double.IsFinite(pole) || pole < 0 || pole >= 1)
            throw new ArgumentOutOfRangeException(nameof(pole), "pole must be in [0, 1)");
    }
}
