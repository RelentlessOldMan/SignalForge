namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Heip's evenness of a record of at least 2 values at least 0, not all 0: the
    /// exponential of the Shannon entropy of the shares, less 1, over n - 1; from 0 to 1
    /// (conventions: Heip's evenness; ADR 0531).</summary>
    /// <param name="samples">Real values, finite, at least 0, not all 0; at least 2.</param>
    /// <returns>Heip's evenness, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double HeipEvenness(ReadOnlySpan<double> samples)
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
        double acc = 0;
        foreach (double v in samples)
        {
            double share = v / total;
            if (share > 0)
                acc += share * Math.Log(share);
        }
        return (Math.Exp(-acc) - 1.0) / (n - 1);
    }
}
