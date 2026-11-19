namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Cohen's kappa: the chance-corrected agreement of two raters' labels
    /// <paramref name="a"/> and <paramref name="b"/> of the same items (conventions: Cohen's
    /// kappa; ADR 0383).</summary>
    /// <param name="a">The first rater's labels; at least 1, finite.</param>
    /// <param name="b">The second rater's labels; the same length as <paramref name="a"/>,
    /// finite.</param>
    /// <returns>Kappa, at most 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or both raters give
    /// every item the same label.</exception>
    public static double CohenKappa(ReadOnlySpan<double> a, ReadOnlySpan<double> b)
    {
        if (a.Length != b.Length)
            throw new ArgumentException("a and b must be the same length", nameof(b));
        if (a.Length < 1)
            throw new ArgumentException("a and b must not be empty", nameof(a));
        long n = a.Length, agree = 0;
        for (int i = 0; i < a.Length; i++)
        {
            if (!double.IsFinite(a[i]) || !double.IsFinite(b[i]))
                throw new ArgumentException("a and b must be finite", nameof(a));
            if (a[i] == b[i])
                agree++;
        }
        double[] sa = a.ToArray(), sb = b.ToArray();
        Array.Sort(sa);
        Array.Sort(sb);
        // Walk the two sorted records together, multiplying the run lengths of equal labels.
        long chance = 0;
        int p = 0, q = 0;
        while (p < sa.Length && q < sb.Length)
        {
            if (sa[p] < sb[q])
            {
                p++;
            }
            else if (sb[q] < sa[p])
            {
                q++;
            }
            else
            {
                double v = sa[p];
                long ra = 0, rb = 0;
                while (p < sa.Length && sa[p] == v)
                {
                    p++;
                    ra++;
                }
                while (q < sb.Length && sb[q] == v)
                {
                    q++;
                    rb++;
                }
                chance += ra * rb;
            }
        }
        if (chance == n * n)
            throw new ArgumentException("both raters give every item the same label", nameof(a));
        return (double)(n * agree - chance) / (n * n - chance);
    }
}
