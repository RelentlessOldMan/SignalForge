namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Jensen–Shannon divergence between the discrete distributions
    /// <paramref name="p"/> and <paramref name="q"/>, each normalized by its own sum, in nats
    /// (conventions: Jensen–Shannon divergence; ADR 0408).</summary>
    /// <param name="p">The first distribution, finite and non-negative, with a positive
    /// sum.</param>
    /// <param name="q">The second distribution, the same length as p, finite and
    /// non-negative, with a positive sum.</param>
    /// <returns>The divergence in nats, from 0 to ln 2.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double JsDivergence(ReadOnlySpan<double> p, ReadOnlySpan<double> q)
    {
        double ps = DistributionSum(p, nameof(p), out double pt);
        double qs = DistributionSum(q, nameof(q), out double qt);
        if (p.Length != q.Length)
            throw new ArgumentException("p and q must have the same length", nameof(q));
        double d = 0;
        for (int i = 0; i < p.Length; i++)
        {
            double pi = p[i] / pt / ps, qi = q[i] / qt / qs;
            double mi = (pi + qi) / 2.0;
            double t = 0;
            if (pi > 0)
                t += pi * Math.Log(pi / mi);
            if (qi > 0)
                t += qi * Math.Log(qi / mi);
            d += t;
        }
        return Math.Min(Math.Max(d / 2.0, 0.0), Math.Log(2.0));
    }
}
