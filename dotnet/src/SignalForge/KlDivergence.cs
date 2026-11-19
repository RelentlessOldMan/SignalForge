namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Kullback–Leibler divergence of the discrete distribution
    /// <paramref name="p"/> from <paramref name="q"/>, each normalized by its own sum, in nats
    /// (conventions: Kullback–Leibler divergence; ADR 0407).</summary>
    /// <param name="p">The first distribution, finite and non-negative, with a positive
    /// sum.</param>
    /// <param name="q">The second distribution, the same length as p, finite and
    /// non-negative, with a positive sum, and not zero where p is not.</param>
    /// <returns>The divergence in nats, zero or more.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double KlDivergence(ReadOnlySpan<double> p, ReadOnlySpan<double> q)
    {
        double ps = DistributionSum(p, nameof(p));
        double qs = DistributionSum(q, nameof(q));
        if (p.Length != q.Length)
            throw new ArgumentException("p and q must have the same length", nameof(q));
        double d = 0;
        for (int i = 0; i < p.Length; i++)
        {
            if (p[i] == 0)
                continue;
            if (q[i] == 0)
                throw new ArgumentException("q is zero where p is not: the divergence is infinite", nameof(q));
            double pi = p[i] / ps, qi = q[i] / qs;
            d += pi * Math.Log(pi / qi);
        }
        return Math.Max(d, 0.0);
    }

    // Checks a discrete distribution and returns its sum, taken in order.
    static double DistributionSum(ReadOnlySpan<double> values, string name)
    {
        if (values.Length < 1)
            throw new ArgumentException($"{name} must not be empty", name);
        double total = 0;
        foreach (double v in values)
        {
            if (!double.IsFinite(v) || v < 0)
                throw new ArgumentException($"{name} must be finite and non-negative", name);
            total += v;
        }
        if (total <= 0)
            throw new ArgumentException($"{name} must have a positive sum", name);
        return total;
    }
}
