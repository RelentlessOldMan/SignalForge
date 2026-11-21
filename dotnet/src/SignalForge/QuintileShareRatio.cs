namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The quintile share ratio of a record of values at least 0: the share of the
    /// largest 20% over the share of the smallest 20%, from the Lorenz curve joined by
    /// straight lines (conventions: the quintile share ratio; ADR 0519).</summary>
    /// <param name="samples">Real values, finite, at least 0, the smallest 20% holding some
    /// of the total; at least 1.</param>
    /// <returns>The quintile share ratio, at least 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double QuintileShareRatio(ReadOnlySpan<double> samples)
    {
        int n = samples.Length;
        if (n < 1)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            if (v < 0)
                throw new ArgumentException("samples must be at least 0", nameof(samples));
        }
        double[] sorted = samples.ToArray();
        Array.Sort(sorted);
        var sums = new double[n + 1];
        for (int k = 0; k < n; k++)
            sums[k + 1] = sums[k] + sorted[k];
        int j2 = Math.DivRem(n, 5, out int r2);
        double low = sums[j2] + (r2 / 5.0 * sorted[j2]);
        if (!(low > 0))
            throw new ArgumentException("the smallest 20% of samples must hold some of the total", nameof(samples));
        int j8 = Math.DivRem(4 * n, 5, out int r8);
        double upto = sums[j8] + (r8 / 5.0 * sorted[j8]);
        return (sums[n] - upto) / low;
    }
}
