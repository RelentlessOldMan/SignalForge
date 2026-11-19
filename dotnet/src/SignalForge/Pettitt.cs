namespace SignalForge;

/// <summary>Pettitt's change-point statistic, where it is reached, and its approximate p-value
/// (conventions: Pettitt change-point test; ADR 0366).</summary>
/// <param name="Statistic">The largest <c>|U_t|</c> over the splits.</param>
/// <param name="Index">The smallest split reaching it: the last sample before the change.</param>
/// <param name="PValue">Pettitt's approximation <c>min(1, 2 exp(−6K²/(N³ + N²)))</c>.</param>
public sealed record Pettitt(long Statistic, int Index, double PValue);

public static partial class Measurements
{
    /// <summary>Pettitt's change-point test: the largest <c>|U_t|</c> over the splits, the last
    /// sample before the change, and the approximate p-value (conventions: Pettitt
    /// change-point test; ADR 0366).</summary>
    /// <param name="samples">Real samples, finite, at least 2.</param>
    /// <returns>The statistic, its location and its p-value.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Pettitt Pettitt(ReadOnlySpan<double> samples)
    {
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        int n = samples.Length;
        if (n < 2)
            throw new ArgumentException("samples must have at least 2 values", nameof(samples));
        long u = 0, best = -1;
        int where = 0;
        for (int t = 0; t < n - 1; t++)
        {
            foreach (double v in samples)
            {
                if (v > samples[t])
                    u++;
                else if (v < samples[t])
                    u--;
            }
            if (Math.Abs(u) > best)
            {
                best = Math.Abs(u);
                where = t;
            }
        }
        double nd = n, k = best;
        double p = Math.Min(1.0, 2 * Math.Exp(-6 * k * k / (nd * nd * nd + nd * nd)));
        return new Pettitt(best, where, p);
    }
}
