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

    /// <summary>Full-wave rectifies real samples, blocks the DC, and blends with the dry signal
    /// (conventions: Octave-up effect; ADR 0289).</summary>
    /// <param name="samples">Real, finite samples, at least one.</param>
    /// <param name="pole">The DC blocker's pole, in [0, 1).</param>
    /// <param name="mix">The wet fraction, in [0, 1].</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] OctaveUp(ReadOnlySpan<double> samples, double pole, double mix)
    {
        CheckMix(mix);
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        double[] r = new double[samples.Length];
        for (int n = 0; n < r.Length; n++)
        {
            if (!double.IsFinite(samples[n]))
                throw new ArgumentException("samples must be finite", nameof(samples));
            r[n] = Math.Abs(samples[n]);
        }
        double[] wet = DcBlocker(r, pole);
        double[] y = new double[r.Length];
        for (int n = 0; n < y.Length; n++)
            y[n] = samples[n] * (1 - mix) + wet[n] * mix;
        return y;
    }

    /// <summary>Multiplies the rectified samples by a sign that flips at each rising zero
    /// crossing, halving the frequency, and blends with the dry signal (conventions: Octave-down
    /// effect; ADR 0291).</summary>
    /// <param name="samples">Real, finite samples, at least one.</param>
    /// <param name="mix">The wet fraction, in [0, 1].</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] OctaveDown(ReadOnlySpan<double> samples, double mix)
    {
        CheckMix(mix);
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        double[] y = new double[samples.Length];
        double sign = 1;
        for (int n = 0; n < y.Length; n++)
        {
            double v = samples[n];
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            if (n > 0 && samples[n - 1] < 0 && v >= 0)
                sign = -sign;
            y[n] = v * (1 - mix) + sign * Math.Abs(v) * mix;
        }
        return y;
    }
}
