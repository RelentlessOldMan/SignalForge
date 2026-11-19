namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Bhattacharyya distance between the discrete distributions
    /// <paramref name="p"/> and <paramref name="q"/>, each normalized by its own sum: minus
    /// the log of their overlap (conventions: Bhattacharyya distance; ADR 0410).</summary>
    /// <param name="p">The first distribution, finite and non-negative, with a positive
    /// sum.</param>
    /// <param name="q">The second distribution, the same length as p, finite and
    /// non-negative, with a positive sum, and positive somewhere p is.</param>
    /// <returns>The distance, zero or more.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double BhattacharyyaDistance(ReadOnlySpan<double> p, ReadOnlySpan<double> q)
    {
        double ps = DistributionSum(p, nameof(p));
        double qs = DistributionSum(q, nameof(q));
        if (p.Length != q.Length)
            throw new ArgumentException("p and q must have the same length", nameof(q));
        double bc = 0;
        for (int i = 0; i < p.Length; i++)
            bc += Math.Sqrt(p[i] / ps * (q[i] / qs));
        if (bc == 0)
            throw new ArgumentException("p and q share no support: the distance is infinite", nameof(q));
        return 0.0 - Math.Log(Math.Min(bc, 1.0));
    }
}
