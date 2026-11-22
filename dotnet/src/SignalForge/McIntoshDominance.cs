namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The McIntosh dominance of a record of values at least 0 totalling more than
    /// 1: the total less the Euclidean length over the total less its square root; 0 when
    /// one value holds the total (conventions: the McIntosh dominance; ADR 0539).</summary>
    /// <param name="samples">Real values, finite, at least 0, totalling more than 1.</param>
    /// <returns>The McIntosh dominance, at least 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double McIntoshDominance(ReadOnlySpan<double> samples)
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
        if (!(total > 1))
            throw new ArgumentException("samples must total more than 1", nameof(samples));
        double sq = 0;
        foreach (double v in samples)
            sq += v * v;
        return (total - Math.Sqrt(sq)) / (total - Math.Sqrt(total));
    }
}
