namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Hutcheson's t between two records of whole numbers at least 0, not all 0: the
    /// difference of their plug-in Shannon entropies over the root of the summed Hutcheson
    /// variances (conventions: Hutcheson's t; ADR 0557).</summary>
    /// <param name="a">The first record: whole numbers at least 0, not all 0, totalling at
    /// most 10 000 000.</param>
    /// <param name="b">The second record, as for <paramref name="a"/>.</param>
    /// <returns>Hutcheson's t; positive when <paramref name="a"/> is the more
    /// diverse.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double HutchesonT(ReadOnlySpan<double> a, ReadOnlySpan<double> b)
    {
        (double hA, double vA) = HutchesonParts(a, nameof(a));
        (double hB, double vB) = HutchesonParts(b, nameof(b));
        double spread = vA + vB;
        if (!(spread > 0))
            throw new ArgumentException("a and b must not both have a single kind", nameof(b));
        return (hA - hB) / Math.Sqrt(spread);
    }

    private static (double Entropy, double Variance) HutchesonParts(ReadOnlySpan<double> x, string name)
    {
        if (x.Length < 1)
            throw new ArgumentException(name + " must not be empty", name);
        double total = 0;
        foreach (double v in x)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException(name + " must be finite", name);
            if (v < 0)
                throw new ArgumentException(name + " must be at least 0", name);
            if (v != Math.Floor(v))
                throw new ArgumentException(name + " must be whole numbers", name);
            total += v;
        }
        if (!(total > 0))
            throw new ArgumentException(name + " must not all be 0", name);
        if (total > 10_000_000)
            throw new ArgumentException(name + " must total at most 10 000 000", name);
        int k = 0;
        double lin = 0;
        double sq = 0;
        foreach (double v in x)
        {
            if (v > 0)
            {
                k++;
                double share = v / total;
                double log = Math.Log(share);
                lin += share * log;
                sq += share * log * log;
            }
        }
        return (-lin, ((sq - (lin * lin)) / total) + ((k - 1) / (2.0 * total * total)));
    }
}
