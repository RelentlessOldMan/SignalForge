namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Permutation entropy with each window weighted by its population variance, over
    /// <c>ln(order!)</c> (conventions: Weighted permutation entropy; ADR 0343).</summary>
    /// <param name="samples">Real samples, finite.</param>
    /// <param name="order">The window length, from 2 to 8.</param>
    /// <param name="delay">The spacing of a window's samples, at least 1.</param>
    /// <returns>The weighted permutation entropy, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or no window varies.</exception>
    public static double WeightedPermutationEntropy(ReadOnlySpan<double> samples, int order, int delay = 1)
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
        samples = ScaledByPowerOf2(samples);
        int windows = samples.Length - ((order - 1) * delay);
        if (windows < 1)
            throw new ArgumentException("samples are too short for one window", nameof(samples));
        var sums = new Dictionary<long, double>();
        var window = new double[order];
        var rank = new int[order];
        double total = 0;
        for (int i = 0; i < windows; i++)
        {
            double mean = 0;
            for (int j = 0; j < order; j++)
            {
                window[j] = samples[i + (j * delay)];
                rank[j] = j;
                mean += window[j];
            }
            mean /= order;
            double weight = 0;
            foreach (double v in window)
                weight += (v - mean) * (v - mean);
            weight /= order;
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
            sums[key] = sums.GetValueOrDefault(key) + weight;
            total += weight;
        }
        if (!(total > 0))
            throw new ArgumentException("at least one window must vary", nameof(samples));
        double factorial = 1;
        for (int k = 2; k <= order; k++)
            factorial *= k;
        double sum = 0;
        foreach (double s in sums.Values)
        {
            double p = s / total;
            if (p > 0)
                sum -= p * Math.Log(p);
        }
        return sum / Math.Log(factorial);
    }
}
