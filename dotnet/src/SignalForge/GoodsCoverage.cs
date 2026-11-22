namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Good's coverage of a record of values at least 0, not all 0: one less the
    /// count of values equal to 1 over the total (conventions: Good's coverage; ADR 0544).
    /// </summary>
    /// <param name="samples">Real values, finite, at least 0, not all 0; at least 1.</param>
    /// <returns>Good's coverage, from 0 to 1 for whole-number counts.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double GoodsCoverage(ReadOnlySpan<double> samples)
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
        int ones = 0;
        foreach (double v in samples)
        {
            if (v == 1)
                ones++;
        }
        return 1.0 - (ones / total);
    }
}
