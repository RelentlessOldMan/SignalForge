namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Jeffreys divergence between the discrete distributions
    /// <paramref name="p"/> and <paramref name="q"/>, each normalized by its own sum: the
    /// Kullback–Leibler divergence both ways, added (conventions: Jeffreys divergence;
    /// ADR 0414).</summary>
    /// <param name="p">The first distribution, finite and non-negative, with a positive
    /// sum.</param>
    /// <param name="q">The second distribution, the same length as p, finite and
    /// non-negative, with a positive sum, and zero exactly where p is.</param>
    /// <returns>The divergence, zero or more.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double JeffreysDivergence(ReadOnlySpan<double> p, ReadOnlySpan<double> q)
    {
        double ps = DistributionSum(p, nameof(p));
        double qs = DistributionSum(q, nameof(q));
        if (p.Length != q.Length)
            throw new ArgumentException("p and q must have the same length", nameof(q));
        double s = 0;
        for (int i = 0; i < p.Length; i++)
        {
            if (p[i] == 0 && q[i] == 0)
                continue;
            if (p[i] == 0 || q[i] == 0)
                throw new ArgumentException("p and q must be zero at the same indices: the divergence is infinite", nameof(q));
            double pi = p[i] / ps, qi = q[i] / qs;
            s += (pi - qi) * Math.Log(pi / qi);
        }
        return s;
    }
}
