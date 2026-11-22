namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Margalef's index of a record of values at least 0 totalling more than 1: one
    /// less than the count of values above 0 over the logarithm of the total (conventions:
    /// Margalef's index; ADR 0542).</summary>
    /// <param name="samples">Real values, finite, at least 0, totalling more than 1.</param>
    /// <returns>Margalef's index, at least 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double MargalefIndex(ReadOnlySpan<double> samples)
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
        int k = 0;
        foreach (double v in samples)
        {
            if (v > 0)
                k++;
        }
        return (k - 1) / Math.Log(total);
    }
}
