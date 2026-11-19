namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Scott's pi: the agreement of two raters' labels <paramref name="a"/> and
    /// <paramref name="b"/> of the same items, corrected for chance from their pooled label
    /// rates (conventions: Scott's pi; ADR 0384).</summary>
    /// <param name="a">The first rater's labels; at least 1, finite.</param>
    /// <param name="b">The second rater's labels; the same length as <paramref name="a"/>,
    /// finite.</param>
    /// <returns>Pi, at most 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or every label in
    /// both records is the same.</exception>
    public static double ScottPi(ReadOnlySpan<double> a, ReadOnlySpan<double> b)
    {
        if (a.Length != b.Length)
            throw new ArgumentException("a and b must be the same length", nameof(b));
        if (a.Length < 1)
            throw new ArgumentException("a and b must not be empty", nameof(a));
        long n = a.Length, agree = 0;
        var all = new double[2 * a.Length];
        for (int i = 0; i < a.Length; i++)
        {
            if (!double.IsFinite(a[i]) || !double.IsFinite(b[i]))
                throw new ArgumentException("a and b must be finite", nameof(a));
            if (a[i] == b[i])
                agree++;
            all[2 * i] = a[i];
            all[2 * i + 1] = b[i];
        }
        Array.Sort(all);
        long pooled = 0;
        for (int i = 0; i < all.Length;)
        {
            int k = i;
            while (k < all.Length && all[k] == all[i])
                k++;
            long t = k - i;
            pooled += t * t;
            i = k;
        }
        if (pooled == 4 * n * n)
            throw new ArgumentException("every label in both records is the same", nameof(a));
        return (double)(4 * n * agree - pooled) / (4 * n * n - pooled);
    }
}
