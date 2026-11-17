using System.Numerics;

namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Teager-Kaiser energy <c>|x[n]|² − Re(x[n−1]·conj x[n+1])</c>, <c>N − 2</c>
    /// values (conventions: Teager-Kaiser energy; ADR 0188).</summary>
    /// <param name="samples">Complex samples, finite, at least three.</param>
    /// <returns>The energy for <c>n = 1 … N−2</c>.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] TeagerEnergy(ReadOnlySpan<Complex> samples)
    {
        if (samples.Length < 3)
            throw new ArgumentException("samples must hold at least three values", nameof(samples));
        foreach (Complex v in samples)
        {
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        var psi = new double[samples.Length - 2];
        for (int n = 1; n < samples.Length - 1; n++)
        {
            Complex m = samples[n];
            psi[n - 1] = m.Real * m.Real + m.Imaginary * m.Imaginary - (samples[n - 1] * Complex.Conjugate(samples[n + 1])).Real;
        }
        return psi;
    }

    /// <summary>The Teager-Kaiser energy <c>x[n]² − x[n−1]·x[n+1]</c>, <c>N − 2</c> values
    /// (conventions: Teager-Kaiser energy; ADR 0188).</summary>
    /// <param name="samples">Real samples, finite, at least three.</param>
    /// <returns>The energy for <c>n = 1 … N−2</c>.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] TeagerEnergy(ReadOnlySpan<double> samples)
    {
        if (samples.Length < 3)
            throw new ArgumentException("samples must hold at least three values", nameof(samples));
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        var psi = new double[samples.Length - 2];
        for (int n = 1; n < samples.Length - 1; n++)
            psi[n - 1] = samples[n] * samples[n] - samples[n - 1] * samples[n + 1];
        return psi;
    }
}
