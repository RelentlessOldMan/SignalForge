namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Cliff's delta: over every pair of a value of <paramref name="x"/> and one of
    /// <paramref name="y"/>, the share where x is larger less the share where it is smaller,
    /// from −1 to 1 (conventions: Cliff's delta; ADR 0400).</summary>
    /// <param name="x">The first sample, finite; at least 1 value.</param>
    /// <param name="y">The second sample, finite; at least 1 value.</param>
    /// <returns>The effect size, from −1 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double CliffDelta(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        CliffCheck(x, nameof(x));
        CliffCheck(y, nameof(y));
        var ys = y.ToArray();
        Array.Sort(ys);
        long below = 0, above = 0;
        foreach (double v in x)
        {
            below += CliffBound(ys, v, false);
            above += ys.Length - CliffBound(ys, v, true);
        }
        return (double)(below - above) / ((long)x.Length * y.Length);
    }

    static void CliffCheck(ReadOnlySpan<double> values, string name)
    {
        if (values.Length < 1)
            throw new ArgumentException($"{name} must not be empty", name);
        foreach (double v in values)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException($"{name} must be finite", name);
        }
    }

    // The number of sorted values below v, or at most v when inclusive.
    static int CliffBound(double[] sorted, double v, bool inclusive)
    {
        int lo = 0, hi = sorted.Length;
        while (lo < hi)
        {
            int mid = lo + (hi - lo) / 2;
            if (sorted[mid] < v || (inclusive && sorted[mid] == v))
                lo = mid + 1;
            else
                hi = mid;
        }
        return lo;
    }
}
