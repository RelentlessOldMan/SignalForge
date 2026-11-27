namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The mean log deviation of a record of positive values: the mean of
    /// ln(mean/x), the Theil L index, at least 0 (conventions: the mean log deviation;
    /// ADR 0514).</summary>
    /// <param name="samples">Real values, finite, greater than 0; at least 1.</param>
    /// <returns>The mean log deviation, at least 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double MeanLogDeviation(ReadOnlySpan<double> samples)
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
            if (!(v > 0))
                throw new ArgumentException("samples must be greater than 0", nameof(samples));
            total += v;
        }
        double mean = total / n;
        double sum = 0;
        foreach (double v in samples)
            sum += Math.Log(mean / v);
        return sum / n;
    }
}
