namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The cross-entropy in nats of the discrete distribution <paramref name="q"/>
    /// under <paramref name="p"/>, each normalized by its own sum (conventions:
    /// cross-entropy; ADR 0415).</summary>
    /// <param name="p">The first distribution, finite and non-negative, with a positive
    /// sum.</param>
    /// <param name="q">The second distribution, the same length as p, finite and
    /// non-negative, with a positive sum, and not zero where p is not.</param>
    /// <returns>The cross-entropy in nats, zero or more.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double CrossEntropy(ReadOnlySpan<double> p, ReadOnlySpan<double> q)
    {
        double ps = DistributionSum(p, nameof(p));
        double qs = DistributionSum(q, nameof(q));
        if (p.Length != q.Length)
            throw new ArgumentException("p and q must have the same length", nameof(q));
        double s = 0;
        for (int i = 0; i < p.Length; i++)
        {
            if (p[i] == 0)
                continue;
            if (q[i] == 0)
                throw new ArgumentException("q is zero where p is not: the cross-entropy is infinite", nameof(q));
            s += p[i] / ps * Math.Log(q[i] / qs);
        }
        return 0.0 - s;
    }
}
