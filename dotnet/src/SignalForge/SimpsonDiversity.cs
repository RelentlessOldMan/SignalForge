namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Gini-Simpson index of a record of values at least 0, not all 0: one less
    /// the sum of the squared shares, from 0 to 1 - 1/n (conventions: the Gini-Simpson index;
    /// ADR 0529).</summary>
    /// <param name="samples">Real values, finite, at least 0, not all 0; at least 1.</param>
    /// <returns>The Gini-Simpson index, from 0 to 1 - 1/n.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double SimpsonDiversity(ReadOnlySpan<double> samples)
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
        double acc = 0;
        foreach (double v in samples)
        {
            double share = v / total;
            acc += share * share;
        }
        return 1.0 - acc;
    }
}
