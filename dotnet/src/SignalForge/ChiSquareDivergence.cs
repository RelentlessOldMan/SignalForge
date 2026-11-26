namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Pearson chi-square divergence of the discrete distribution
    /// <paramref name="p"/> from <paramref name="q"/>, each normalized by its own sum
    /// (conventions: Pearson chi-square divergence; ADR 0412).</summary>
    /// <param name="p">The first distribution, finite and non-negative, with a positive
    /// sum.</param>
    /// <param name="q">The second distribution, the same length as p, finite and
    /// non-negative, with a positive sum, and not zero where p is not.</param>
    /// <returns>The divergence, zero or more.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double ChiSquareDivergence(ReadOnlySpan<double> p, ReadOnlySpan<double> q)
    {
        double ps = DistributionSum(p, nameof(p), out double pt);
        double qs = DistributionSum(q, nameof(q), out double qt);
        if (p.Length != q.Length)
            throw new ArgumentException("p and q must have the same length", nameof(q));
        double s = 0;
        for (int i = 0; i < p.Length; i++)
        {
            if (q[i] == 0)
            {
                if (p[i] > 0)
                    throw new ArgumentException("q is zero where p is not: the divergence is infinite", nameof(q));
                continue;
            }
            double qi = q[i] / qt / qs;
            double d = p[i] / pt / ps - qi;
            s += d * d / qi;
        }
        return s;
    }
}
