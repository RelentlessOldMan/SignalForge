namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Palma ratio of a record of values at least 0: the share of the largest
    /// 10% over the share of the smallest 40%, from the Lorenz curve joined by straight
    /// lines (conventions: the Palma ratio; ADR 0518).</summary>
    /// <param name="samples">Real values, finite, at least 0, the smallest 40% holding some
    /// of the total; at least 1.</param>
    /// <returns>The Palma ratio, greater than 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double PalmaRatio(ReadOnlySpan<double> samples)
    {
        int n = samples.Length;
        if (n < 1)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        samples = ScaledToLargest(samples);
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
        int j4 = Math.DivRem(2 * n, 5, out int r4);
        double low = sums[j4] + (r4 / 5.0 * sorted[j4]);
        if (!(low > 0))
            throw new ArgumentException("the smallest 40% of samples must hold some of the total", nameof(samples));
        int j9 = Math.DivRem(9 * n, 10, out int r9);
        double upto = sums[j9] + (r9 / 10.0 * sorted[j9]);
        return (sums[n] - upto) / low;
    }
}
