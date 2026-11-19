namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Kendall's tau-b: the concordant pairs less the discordant ones, over the
    /// tie-corrected count of pairs (conventions: Kendall's tau-b; ADR 0370).</summary>
    /// <param name="x">Real samples, finite, at least 2 and not all equal.</param>
    /// <param name="y">Real samples, finite, as many as <paramref name="x"/> and not all
    /// equal.</param>
    /// <returns>Tau-b, from −1 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double KendallTau(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        foreach (double v in x)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("x must be finite", nameof(x));
        }
        foreach (double v in y)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("y must be finite", nameof(y));
        }
        int n = x.Length;
        if (y.Length != n)
            throw new ArgumentException("x and y must be the same length", nameof(y));
        if (n < 2)
            throw new ArgumentException("x and y must have at least 2 values", nameof(x));
        long s = 0;
        for (int i = 0; i < n - 1; i++)
        {
            for (int j = i + 1; j < n; j++)
                s += Math.Sign(x[j] - x[i]) * Math.Sign(y[j] - y[i]);
        }
        long n0 = (long)n * (n - 1) / 2;
        long n1 = KendallTiedPairs(x, nameof(x)), n2 = KendallTiedPairs(y, nameof(y));
        return s / Math.Sqrt((double)(n0 - n1) * (n0 - n2));
    }

    static long KendallTiedPairs(ReadOnlySpan<double> samples, string name)
    {
        var keys = samples.ToArray();
        Array.Sort(keys);
        if (keys[0] == keys[^1])
            throw new ArgumentException("neither x nor y may have every value equal", name);
        long pairs = 0;
        for (int i = 0; i < keys.Length;)
        {
            int j = i;
            while (j + 1 < keys.Length && keys[j + 1] == keys[i])
                j++;
            long t = j - i + 1;
            pairs += t * (t - 1) / 2;
            i = j + 1;
        }
        return pairs;
    }
}
