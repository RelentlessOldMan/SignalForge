namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Theil index of a record of values at least 0, not all 0: the mean of
    /// (x/mean) ln(x/mean), 0 for a value of 0, from 0 to ln n (conventions: the Theil index;
    /// ADR 0511).</summary>
    /// <param name="samples">Real values, finite, at least 0, not all 0; at least 1.</param>
    /// <returns>The Theil index, from 0 to ln n.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double TheilIndex(ReadOnlySpan<double> samples)
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
        double mean = total / n;
        double sum = 0;
        foreach (double v in samples)
        {
            if (v > 0)
            {
                double ratio = v / mean;
                sum += ratio * Math.Log(ratio);
            }
        }
        return sum / n;
    }
}
