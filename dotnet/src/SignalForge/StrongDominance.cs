namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Strong's dominance of a record of values at least 0, not all 0: the largest
    /// gap between the share held by the i largest values and i over the count of values
    /// above 0 (conventions: Strong's dominance; ADR 0549).</summary>
    /// <param name="samples">Real values, finite, at least 0, not all 0; at least 1.</param>
    /// <returns>Strong's dominance, from 0 to below 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double StrongDominance(ReadOnlySpan<double> samples)
    {
        int n = samples.Length;
        if (n < 1)
            throw new ArgumentException("samples must not be empty", nameof(samples));
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
        int k = 0;
        foreach (double v in sorted)
        {
            if (v > 0)
                k++;
        }
        double best = 0;
        double run = 0;
        for (int i = 1; i <= k; i++)
        {
            run += sorted[n - i];
            best = Math.Max(best, (run / total) - ((double)i / k));
        }
        return best;
    }
}
