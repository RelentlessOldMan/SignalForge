namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Hoover index of a record of values at least 0, not all 0: the sum of the
    /// absolute deviations from the mean over twice the total, from 0 to 1 - 1/n
    /// (conventions: the Hoover index; ADR 0512).</summary>
    /// <param name="samples">Real values, finite, at least 0, not all 0; at least 1.</param>
    /// <returns>The Hoover index, from 0 to 1 - 1/n.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double HooverIndex(ReadOnlySpan<double> samples)
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
        double dev = 0;
        foreach (double v in samples)
            dev += Math.Abs(v - mean);
        return dev / (2.0 * total);
    }
}
