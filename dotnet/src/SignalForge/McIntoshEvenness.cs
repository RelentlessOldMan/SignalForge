namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The McIntosh evenness of a record of at least 2 values at least 0, not all 0:
    /// the total less the Euclidean length over the total less the total over the square
    /// root of n; from 0 to 1 (conventions: the McIntosh evenness; ADR 0540).</summary>
    /// <param name="samples">Real values, finite, at least 0, not all 0; at least 2.</param>
    /// <returns>The McIntosh evenness, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double McIntoshEvenness(ReadOnlySpan<double> samples)
    {
        int n = samples.Length;
        if (n < 2)
            throw new ArgumentException("samples must have at least 2 values", nameof(samples));
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
        double sq = 0;
        foreach (double v in samples)
            sq += v * v;
        return (total - Math.Sqrt(sq)) / (total - (total / Math.Sqrt(n)));
    }
}
