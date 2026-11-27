namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Sheldon's evenness of a record of values at least 0, not all 0: the
    /// exponential of the Shannon entropy of the shares over n, from 1/n to 1 (conventions:
    /// Sheldon's evenness; ADR 0538).</summary>
    /// <param name="samples">Real values, finite, at least 0, not all 0; at least 1.</param>
    /// <returns>Sheldon's evenness, from 1/n to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double SheldonEvenness(ReadOnlySpan<double> samples)
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
            if (share > 0)
                acc += share * Math.Log(share);
        }
        return Math.Exp(-acc) / n;
    }
}
