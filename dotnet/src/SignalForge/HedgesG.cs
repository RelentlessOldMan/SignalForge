namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Hedges' g: Cohen's d of <paramref name="x"/> and <paramref name="y"/> times the
    /// exact small-sample correction J(m) = Γ(m/2)/(√(m/2)·Γ((m − 1)/2)), m = n_x + n_y − 2
    /// (conventions: Hedges' g; ADR 0398).</summary>
    /// <param name="x">The first sample, finite; at least 2 values.</param>
    /// <param name="y">The second sample, finite; at least 2 values.</param>
    /// <returns>The corrected effect size.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or the pooled standard
    /// deviation is zero.</exception>
    public static double HedgesG(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        double d = CohenD(x, y);
        double m = x.Length + y.Length - 2;
        double j = Math.Exp(SpecialFunctions.LogGamma(m / 2) - SpecialFunctions.LogGamma((m - 1) / 2)) / Math.Sqrt(m / 2);
        return j * d;
    }
}
