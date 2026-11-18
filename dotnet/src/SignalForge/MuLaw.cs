namespace SignalForge;

public static partial class Dsp
{
    /// <summary>Continuous μ-law compression <c>sign(x)·ln(1 + μ|x|)/ln(1 + μ)</c> on
    /// <c>[−1, 1]</c> (conventions: μ-law companding; ADR 0248).</summary>
    /// <param name="samples">Finite samples in <c>[−1, 1]</c>, at least one.</param>
    /// <param name="mu">The compression parameter <c>μ</c>, finite and positive.</param>
    /// <returns>One compressed value per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] MuLawCompress(ReadOnlySpan<double> samples, double mu = 255.0)
    {
        CheckMuLaw(samples, mu);
        double den = double.LogP1(mu);
        var y = new double[samples.Length];
        for (int n = 0; n < y.Length; n++)
            y[n] = Math.Sign(samples[n]) * (double.LogP1(mu * Math.Abs(samples[n])) / den);
        return y;
    }

    /// <summary>Continuous μ-law expansion <c>sign(y)·((1 + μ)^|y| − 1)/μ</c> on <c>[−1, 1]</c>,
    /// the inverse of <see cref="MuLawCompress"/> (conventions: μ-law companding; ADR 0248).</summary>
    /// <param name="samples">Finite samples in <c>[−1, 1]</c>, at least one.</param>
    /// <param name="mu">The compression parameter <c>μ</c>, finite and positive.</param>
    /// <returns>One expanded value per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] MuLawExpand(ReadOnlySpan<double> samples, double mu = 255.0)
    {
        CheckMuLaw(samples, mu);
        double l = double.LogP1(mu);
        var x = new double[samples.Length];
        for (int n = 0; n < x.Length; n++)
            x[n] = Math.Sign(samples[n]) * (double.ExpM1(Math.Abs(samples[n]) * l) / mu);
        return x;
    }

    private static void CheckMuLaw(ReadOnlySpan<double> samples, double mu)
    {
        if (!double.IsFinite(mu) || !(mu > 0))
            throw new ArgumentOutOfRangeException(nameof(mu), "mu must be positive");
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            if (Math.Abs(v) > 1)
                throw new ArgumentException("samples must be within [-1, 1]", nameof(samples));
        }
    }
}
