namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Menhinick's index of a record of values at least 0, not all 0: the count of
    /// values above 0 over the square root of the total (conventions: Menhinick's index;
    /// ADR 0541).</summary>
    /// <param name="samples">Real values, finite, at least 0, not all 0; at least 1.</param>
    /// <returns>Menhinick's index, above 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double MenhinickIndex(ReadOnlySpan<double> samples)
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
        foreach (double v in samples)
        {
            if (v > 0)
                k++;
        }
        return k / Math.Sqrt(total);
    }
}
