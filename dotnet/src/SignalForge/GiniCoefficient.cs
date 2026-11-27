namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Gini coefficient of a record of values at least 0, not all 0: the mean
    /// absolute difference over all ordered pairs over twice the mean, from 0 to 1 - 1/n
    /// (conventions: the Gini coefficient; ADR 0510).</summary>
    /// <param name="samples">Real values, finite, at least 0, not all 0; at least 1.</param>
    /// <returns>The Gini coefficient, from 0 to 1 - 1/n.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double GiniCoefficient(ReadOnlySpan<double> samples)
    {
        int n = samples.Length;
        if (n < 1)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        samples = ScaledToLargest(samples);
        double total = 0;
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            if (v < 0)
                throw new ArgumentException("samples must be at least 0", nameof(samples));
            total += v;
        }
        if (!(total > 0))
            throw new ArgumentException("samples must not all be 0", nameof(samples));
        double[] sorted = samples.ToArray();
        Array.Sort(sorted);
        double num = 0;
        for (int k = 0; k < n; k++)
            num += ((2.0 * k) - n + 1) * sorted[k];
        return num / (n * total);
    }
}
