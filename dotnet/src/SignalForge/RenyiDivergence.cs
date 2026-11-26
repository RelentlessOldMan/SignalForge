namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The order-<paramref name="alpha"/> Rényi divergence of the discrete
    /// distribution <paramref name="p"/> from <paramref name="q"/>, each normalized by its own
    /// sum (conventions: Rényi divergence; ADR 0413).</summary>
    /// <param name="p">The first distribution, finite and non-negative, with a positive
    /// sum.</param>
    /// <param name="q">The second distribution, the same length as p, finite and
    /// non-negative, with a positive sum.</param>
    /// <param name="alpha">The order, finite, above 0 and not 1.</param>
    /// <returns>The divergence, zero or more.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or the divergence is
    /// infinite.</exception>
    public static double RenyiDivergence(ReadOnlySpan<double> p, ReadOnlySpan<double> q, double alpha)
    {
        if (!double.IsFinite(alpha) || !(alpha > 0) || alpha == 1)
            throw new ArgumentOutOfRangeException(nameof(alpha), alpha, "must be finite, above 0 and not 1");
        double ps = DistributionSum(p, nameof(p), out double pt);
        double qs = DistributionSum(q, nameof(q), out double qt);
        if (p.Length != q.Length)
            throw new ArgumentException("p and q must have the same length", nameof(q));
        double s = 0;
        for (int i = 0; i < p.Length; i++)
        {
            if (p[i] == 0)
                continue;
            if (q[i] == 0)
            {
                if (alpha > 1)
                    throw new ArgumentException("q is zero where p is not: the divergence is infinite", nameof(q));
                continue;
            }
            s += Math.Pow(p[i] / pt / ps, alpha) * Math.Pow(q[i] / qt / qs, 1.0 - alpha);
        }
        if (s == 0)
            throw new ArgumentException("p and q share no support: the divergence is infinite", nameof(q));
        double r = Math.Log(s) / (alpha - 1.0);
        return r > 0 ? r : 0.0;
    }
}
