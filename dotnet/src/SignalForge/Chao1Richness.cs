namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The bias-corrected Chao1 richness of a record of values at least 0, not all
    /// 0: the count of values above 0 plus a term in the counts of values equal to 1 and to
    /// 2 (conventions: the Chao1 richness; ADR 0545).</summary>
    /// <param name="samples">Real values, finite, at least 0, not all 0; at least 1.</param>
    /// <returns>The Chao1 richness, at least the count of values above 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double Chao1Richness(ReadOnlySpan<double> samples)
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
        int k = 0;
        int ones = 0;
        int twos = 0;
        foreach (double v in samples)
        {
            if (v > 0)
                k++;
            if (v == 1)
                ones++;
            else if (v == 2)
                twos++;
        }
        return k + ((double)ones * (ones - 1) / (2.0 * (twos + 1)));
    }
}
