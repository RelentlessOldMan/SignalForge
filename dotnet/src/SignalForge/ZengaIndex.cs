namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Zenga index of a record of at least 2 values at least 0, not all 0: the
    /// mean over k &lt; n of the gap between the mean of the n - k largest and the mean of
    /// the k smallest, over the former, from 0 to 1 (conventions: the Zenga index;
    /// ADR 0521).</summary>
    /// <param name="samples">Real values, finite, at least 0, not all 0; at least 2.</param>
    /// <returns>The Zenga index, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double ZengaIndex(ReadOnlySpan<double> samples)
    {
        int n = samples.Length;
        if (n < 2)
            throw new ArgumentException("samples must have at least 2 values", nameof(samples));
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
        var sums = new double[n];
        double run = 0;
        for (int k = 0; k < n; k++)
        {
            run += sorted[k];
            sums[k] = run;
        }
        if (!(run > 0))
            throw new ArgumentException("samples must not all be 0", nameof(samples));
        double acc = 0;
        for (int k = 1; k < n; k++)
        {
            double low = sums[k - 1];
            acc += low / k / ((run - low) / (n - k));
        }
        return 1.0 - (acc / (n - 1));
    }
}
