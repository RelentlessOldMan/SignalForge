namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Wolfson polarization index of a record of values at least 0 with a median
    /// above 0: 2 (mean/median) (1 - 2 L(1/2) - G), from the Lorenz curve joined by straight
    /// lines and the Gini coefficient; at least 0 (conventions: the Wolfson polarization
    /// index; ADR 0522).</summary>
    /// <param name="samples">Real values, finite, at least 0, the median above 0; at least
    /// 1.</param>
    /// <returns>The Wolfson polarization index, at least 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double WolfsonIndex(ReadOnlySpan<double> samples)
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
        int j = Math.DivRem(n, 2, out int rem);
        double med = rem == 1 ? sorted[j] : (sorted[j - 1] + sorted[j]) / 2;
        if (!(med > 0))
            throw new ArgumentException("the median of samples must be above 0", nameof(samples));
        double total = 0;
        double g = 0;
        double half = 0;
        for (int k = 0; k < n; k++)
        {
            if (k == j)
                half = total;
            double a = sorted[k];
            total += a;
            g += (2 * k - n + 1) * a;
        }
        half += rem / 2.0 * sorted[j];
        return 2.0 * (total - (2.0 * half) - (g / n)) / (n * med);
    }
}
