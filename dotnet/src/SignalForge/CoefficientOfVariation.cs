namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The coefficient of variation of a record with a positive mean: the
    /// population standard deviation, over n, over the mean (conventions: the coefficient of
    /// variation; ADR 0513).</summary>
    /// <param name="samples">Real values, finite, with a mean greater than 0; at least 1.</param>
    /// <returns>The coefficient of variation, at least 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double CoefficientOfVariation(ReadOnlySpan<double> samples)
    {
        int n = samples.Length;
        if (n < 1)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        double total = 0;
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            total += v;
        }
        double mean = total / n;
        if (!(mean > 0))
            throw new ArgumentException("samples must have a mean greater than 0", nameof(samples));
        double ss = 0;
        foreach (double v in samples)
            ss += (v - mean) * (v - mean);
        return Math.Sqrt(ss / n) / mean;
    }
}
