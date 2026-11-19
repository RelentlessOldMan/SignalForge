namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The total variation distance between the discrete distributions
    /// <paramref name="p"/> and <paramref name="q"/>, each normalized by its own sum: half
    /// their L1 distance, from 0 to 1 (conventions: total variation distance; ADR 0411).</summary>
    /// <param name="p">The first distribution, finite and non-negative, with a positive
    /// sum.</param>
    /// <param name="q">The second distribution, the same length as p, finite and
    /// non-negative, with a positive sum.</param>
    /// <returns>The distance, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double TotalVariationDistance(ReadOnlySpan<double> p, ReadOnlySpan<double> q)
    {
        double ps = DistributionSum(p, nameof(p));
        double qs = DistributionSum(q, nameof(q));
        if (p.Length != q.Length)
            throw new ArgumentException("p and q must have the same length", nameof(q));
        double s = 0;
        for (int i = 0; i < p.Length; i++)
            s += Math.Abs(p[i] / ps - q[i] / qs);
        return Math.Min(s / 2.0, 1.0);
    }
}
