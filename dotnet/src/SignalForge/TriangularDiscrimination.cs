namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The triangular discrimination between the discrete distributions
    /// <paramref name="p"/> and <paramref name="q"/>, each normalized by its own sum, from 0
    /// to 2 (conventions: triangular discrimination; ADR 0416).</summary>
    /// <param name="p">The first distribution, finite and non-negative, with a positive
    /// sum.</param>
    /// <param name="q">The second distribution, the same length as p, finite and
    /// non-negative, with a positive sum.</param>
    /// <returns>The discrimination, from 0 to 2.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double TriangularDiscrimination(ReadOnlySpan<double> p, ReadOnlySpan<double> q)
    {
        double ps = DistributionSum(p, nameof(p), out double pt);
        double qs = DistributionSum(q, nameof(q), out double qt);
        if (p.Length != q.Length)
            throw new ArgumentException("p and q must have the same length", nameof(q));
        double s = 0;
        for (int i = 0; i < p.Length; i++)
        {
            if (p[i] == 0 && q[i] == 0)
                continue;
            double pi = p[i] / pt / ps, qi = q[i] / qt / qs;
            double d = pi - qi;
            s += d * d / (pi + qi);
        }
        return Math.Min(s, 2.0);
    }
}
