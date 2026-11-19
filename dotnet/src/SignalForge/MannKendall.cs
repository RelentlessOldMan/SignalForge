namespace SignalForge;

/// <summary>The Mann–Kendall statistic and its continuity-corrected z-score (conventions:
/// Mann–Kendall trend test; ADR 0364).</summary>
/// <param name="S">The number of rising pairs less the number of falling pairs.</param>
/// <param name="Z">The z-score of <paramref name="S"/> with the tie-corrected variance and a
/// continuity correction of 1.</param>
public sealed record MannKendall(long S, double Z);

public static partial class Measurements
{
    /// <summary>The Mann–Kendall trend test: <c>S</c>, the number of rising pairs less the
    /// falling ones, and its tie-corrected, continuity-corrected z-score (conventions:
    /// Mann–Kendall trend test; ADR 0364).</summary>
    /// <param name="samples">Real samples, finite, at least 2 and not all equal.</param>
    /// <returns>The statistic and its z-score.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static MannKendall MannKendall(ReadOnlySpan<double> samples)
    {
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        int n = samples.Length;
        if (n < 2)
            throw new ArgumentException("samples must have at least 2 values", nameof(samples));
        var sorted = samples.ToArray();
        Array.Sort(sorted);
        if (sorted[0] == sorted[n - 1])
            throw new ArgumentException("samples must not all be equal", nameof(samples));
        double ties = 0;
        for (int i = 0; i < n;)
        {
            int j = i;
            while (j + 1 < n && sorted[j + 1] == sorted[i])
                j++;
            double t = j - i + 1;
            ties += t * (t - 1) * (2 * t + 5);
            i = j + 1;
        }
        long s = 0;
        for (int i = 0; i < n - 1; i++)
        {
            for (int j = i + 1; j < n; j++)
            {
                if (samples[j] > samples[i])
                    s++;
                else if (samples[j] < samples[i])
                    s--;
            }
        }
        double nd = n;
        double variance = (nd * (nd - 1) * (2 * nd + 5) - ties) / 18;
        double z = s == 0 ? 0 : (s > 0 ? s - 1 : s + 1) / Math.Sqrt(variance);
        return new MannKendall(s, z);
    }
}
