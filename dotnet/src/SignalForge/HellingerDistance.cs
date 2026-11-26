namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Hellinger distance between the discrete distributions
    /// <paramref name="p"/> and <paramref name="q"/>, each normalized by its own sum, from 0
    /// to 1 (conventions: Hellinger distance; ADR 0409).</summary>
    /// <param name="p">The first distribution, finite and non-negative, with a positive
    /// sum.</param>
    /// <param name="q">The second distribution, the same length as p, finite and
    /// non-negative, with a positive sum.</param>
    /// <returns>The distance, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double HellingerDistance(ReadOnlySpan<double> p, ReadOnlySpan<double> q)
    {
        double ps = DistributionSum(p, nameof(p), out double pt);
        double qs = DistributionSum(q, nameof(q), out double qt);
        if (p.Length != q.Length)
            throw new ArgumentException("p and q must have the same length", nameof(q));
        double ss = 0;
        for (int i = 0; i < p.Length; i++)
        {
            double d = Math.Sqrt(p[i] / pt / ps) - Math.Sqrt(q[i] / qt / qs);
            ss += d * d;
        }
        return Math.Min(Math.Sqrt(ss / 2.0), 1.0);
    }
}
