namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Chao-Jost coverage of a record of whole numbers at least 0 totalling more
    /// than 1: Good's coverage corrected with the counts of values equal to 1 and to 2
    /// (conventions: the Chao-Jost coverage; ADR 0553).</summary>
    /// <param name="samples">Whole numbers at least 0, totalling more than 1 and at most
    /// 10 000 000.</param>
    /// <returns>The Chao-Jost coverage, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double ChaoJostCoverage(ReadOnlySpan<double> samples)
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
            if (v != Math.Floor(v))
                throw new ArgumentException("samples must be whole numbers", nameof(samples));
            total += v;
        }
        if (!(total > 0))
            throw new ArgumentException("samples must not all be 0", nameof(samples));
        if (total > 10_000_000)
            throw new ArgumentException("samples must total at most 10 000 000", nameof(samples));
        if (!(total > 1))
            throw new ArgumentException("samples must total more than 1", nameof(samples));
        int ones = 0;
        int twos = 0;
        foreach (double v in samples)
        {
            if (v == 1)
                ones++;
            else if (v == 2)
                twos++;
        }
        if (ones == 0)
            return 1.0;
        double a = (total - 1.0) * ones;
        return 1.0 - (ones / total * (a / (a + (2.0 * twos))));
    }
}
