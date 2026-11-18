namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Shannon entropy of the ordinal patterns of <paramref name="order"/> samples
    /// <paramref name="delay"/> apart, over <c>ln(order!)</c> (conventions: Permutation entropy;
    /// ADR 0325).</summary>
    /// <param name="samples">Real samples, finite, long enough for one window.</param>
    /// <param name="order">The pattern length, from 2 to 8.</param>
    /// <param name="delay">The spacing of a window's samples, at least 1.</param>
    /// <returns>The normalized entropy, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double PermutationEntropy(ReadOnlySpan<double> samples, int order, int delay = 1)
    {
        if (order < 2 || order > 8)
            throw new ArgumentOutOfRangeException(nameof(order), order, "must be from 2 to 8");
        if (delay < 1)
            throw new ArgumentOutOfRangeException(nameof(delay), delay, "must be at least 1");
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        int windows = samples.Length - ((order - 1) * delay);
        if (windows < 1)
            throw new ArgumentException("samples are too short for one window", nameof(samples));
        var counts = new Dictionary<long, int>();
        var window = new double[order];
        var rank = new int[order];
        for (int i = 0; i < windows; i++)
        {
            for (int j = 0; j < order; j++)
            {
                window[j] = samples[i + (j * delay)];
                rank[j] = j;
            }
            // Insertion sort is stable: equal values keep their index order.
            for (int j = 1; j < order; j++)
            {
                int r = rank[j];
                int k = j - 1;
                while (k >= 0 && window[rank[k]] > window[r])
                {
                    rank[k + 1] = rank[k];
                    k--;
                }
                rank[k + 1] = r;
            }
            long key = 0;
            for (int j = 0; j < order; j++)
                key = (key * order) + rank[j];
            counts[key] = counts.TryGetValue(key, out int c) ? c + 1 : 1;
        }
        double factorial = 1;
        for (int k = 2; k <= order; k++)
            factorial *= k;
        double sum = 0;
        foreach (int c in counts.Values)
        {
            double p = (double)c / windows;
            sum -= p * Math.Log(p);
        }
        return sum / Math.Log(factorial);
    }
}
