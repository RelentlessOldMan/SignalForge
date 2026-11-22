namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Brillouin index of a record of whole numbers at least 0, not all 0, in
    /// nats: the logarithm of the multinomial coefficient of the counts over their total
    /// (conventions: the Brillouin index; ADR 0546).</summary>
    /// <param name="samples">Whole numbers at least 0, not all 0, totalling at most
    /// 10 000 000; at least 1.</param>
    /// <returns>The Brillouin index in nats, at least 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double BrillouinIndex(ReadOnlySpan<double> samples)
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
        double parts = 0;
        foreach (double v in samples)
        {
            for (int j = 2; j <= (int)v; j++)
                parts += Math.Log(j);
        }
        double whole = 0;
        for (int j = 2; j <= (int)total; j++)
            whole += Math.Log(j);
        return (whole - parts) / total;
    }
}
