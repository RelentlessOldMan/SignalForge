namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Kwoka dominance index of a record of values at least 0, not all 0: the
    /// sum of the squared gaps between neighbouring shares ranked from the largest, from 0
    /// to 1 (conventions: the Kwoka dominance index; ADR 0526).</summary>
    /// <param name="samples">Real values, finite, at least 0, not all 0; at least 1.</param>
    /// <returns>The Kwoka dominance index, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double KwokaDominanceIndex(ReadOnlySpan<double> samples)
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
        double[] sorted = samples.ToArray();
        Array.Sort(sorted);
        double acc = 0;
        for (int i = n - 1; i > 0; i--)
        {
            double gap = (sorted[i] - sorted[i - 1]) / total;
            acc += gap * gap;
        }
        return acc;
    }
}
