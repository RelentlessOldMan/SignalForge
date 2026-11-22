namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Brillouin evenness of a record of whole numbers at least 0, at least 2
    /// above 0: the Brillouin index over its largest value for the same total and count of
    /// kinds (conventions: the Brillouin evenness; ADR 0547).</summary>
    /// <param name="samples">Whole numbers at least 0, at least 2 above 0, totalling at
    /// most 10 000 000.</param>
    /// <returns>The Brillouin evenness, above 0 and at most 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double BrillouinEvenness(ReadOnlySpan<double> samples)
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
        int k = 0;
        double parts = 0;
        foreach (double v in samples)
        {
            if (v > 0)
                k++;
            for (int j = 2; j <= (int)v; j++)
                parts += Math.Log(j);
        }
        if (k < 2)
            throw new ArgumentException("samples must have at least 2 values above 0", nameof(samples));
        double whole = 0;
        for (int j = 2; j <= (int)total; j++)
            whole += Math.Log(j);
        int c = (int)total / k;
        int rem = (int)total - (c * k);
        double low = 0;
        for (int j = 2; j <= c; j++)
            low += Math.Log(j);
        double high = low + Math.Log(c + 1);
        return (whole - parts) / (whole - ((k - rem) * low) - (rem * high));
    }
}
