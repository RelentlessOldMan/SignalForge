namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Berger-Parker index of a record of values at least 0, not all 0: the
    /// largest share of the total, from 1/n to 1 (conventions: the Berger-Parker index;
    /// ADR 0530).</summary>
    /// <param name="samples">Real values, finite, at least 0, not all 0; at least 1.</param>
    /// <returns>The Berger-Parker index, from 1/n to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double BergerParkerIndex(ReadOnlySpan<double> samples)
    {
        int n = samples.Length;
        if (n < 1)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        double total = 0;
        double largest = 0;
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            if (v < 0)
                throw new ArgumentException("samples must be at least 0", nameof(samples));
            total += v;
            largest = Math.Max(largest, v);
        }
        if (!(total > 0))
            throw new ArgumentException("samples must not all be 0", nameof(samples));
        return largest / total;
    }
}
