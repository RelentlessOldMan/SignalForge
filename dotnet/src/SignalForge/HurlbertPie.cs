namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Hurlbert's PIE of a record of values at least 0 totalling more than 1: the
    /// Gini-Simpson index times N/(N - 1), the chance that two individuals drawn without
    /// replacement differ in kind (conventions: Hurlbert's PIE; ADR 0548).</summary>
    /// <param name="samples">Real values, finite, at least 0, totalling more than 1.</param>
    /// <returns>Hurlbert's PIE, at least 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double HurlbertPie(ReadOnlySpan<double> samples)
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
        double acc = 0;
        foreach (double v in samples)
        {
            double share = v / total;
            acc += share * share;
        }
        return total / (total - 1.0) * (1.0 - acc);
    }
}
