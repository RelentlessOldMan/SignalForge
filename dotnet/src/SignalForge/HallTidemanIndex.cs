namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Hall-Tideman index of a record of values at least 0, not all 0: one over
    /// twice the rank-weighted sum of the shares, ranked from the largest, less 1; from 1/n
    /// to 1 (conventions: the Hall-Tideman index; ADR 0525).</summary>
    /// <param name="samples">Real values, finite, at least 0, not all 0; at least 1.</param>
    /// <returns>The Hall-Tideman index, from 1/n to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double HallTidemanIndex(ReadOnlySpan<double> samples)
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
        if (!(total > 0))
            throw new ArgumentException("samples must not all be 0", nameof(samples));
        double[] sorted = samples.ToArray();
        Array.Sort(sorted);
        double acc = 0;
        for (int rank = 1; rank <= n; rank++)
            acc += rank * sorted[n - rank];
        return total / ((2.0 * acc) - total);
    }
}
