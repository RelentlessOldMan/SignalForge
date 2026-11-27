namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The concentration ratio of a record of values at least 0, not all 0: the
    /// share of the total held by the k largest values, from k/n to 1 (conventions: the
    /// concentration ratio; ADR 0524).</summary>
    /// <param name="samples">Real values, finite, at least 0, not all 0; at least 1.</param>
    /// <param name="k">How many of the largest values, from 1 to the number of
    /// samples.</param>
    /// <returns>The concentration ratio, from k/n to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double ConcentrationRatio(ReadOnlySpan<double> samples, int k)
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
        if (k < 1 || k > n)
            throw new ArgumentOutOfRangeException(nameof(k), "k must be from 1 to the number of samples");
        if (!(total > 0))
            throw new ArgumentException("samples must not all be 0", nameof(samples));
        double[] sorted = samples.ToArray();
        Array.Sort(sorted);
        double top = 0;
        for (int i = 0; i < k; i++)
            top += sorted[n - 1 - i];
        return top / total;
    }
}
