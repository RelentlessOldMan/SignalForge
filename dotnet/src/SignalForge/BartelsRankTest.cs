namespace SignalForge;

/// <summary>The von Neumann ratio of the ranks and its z-score against a random record
/// (conventions: Bartels rank test; ADR 0363).</summary>
/// <param name="Ratio">The von Neumann ratio of the ranks, ties given their mean rank.</param>
/// <param name="Z">The z-score of <paramref name="Ratio"/> against 2 with Bartels's
/// variance.</param>
public sealed record BartelsRankTest(double Ratio, double Z);

public static partial class Measurements
{
    /// <summary>Bartels's rank test of randomness: the von Neumann ratio of the ranks, ties
    /// given their mean rank, and its z-score against 2 (conventions: Bartels rank test;
    /// ADR 0363).</summary>
    /// <param name="samples">Real samples, finite, at least 3 and not all equal.</param>
    /// <returns>The ratio and its z-score.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static BartelsRankTest BartelsRankTest(ReadOnlySpan<double> samples)
    {
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        int n = samples.Length;
        if (n < 3)
            throw new ArgumentException("samples must have at least 3 values", nameof(samples));
        var order = new int[n];
        for (int i = 0; i < n; i++)
            order[i] = i;
        var keys = samples.ToArray();
        Array.Sort(keys, order);
        if (keys[0] == keys[n - 1])
            throw new ArgumentException("samples must not all be equal", nameof(samples));
        var rank = new double[n];
        for (int i = 0; i < n;)
        {
            int j = i;
            while (j + 1 < n && keys[j + 1] == keys[i])
                j++;
            double mean = (i + j) / 2.0 + 1;
            for (int k = i; k <= j; k++)
                rank[order[k]] = mean;
            i = j + 1;
        }
        double centre = (n + 1) / 2.0, den = 0, num = 0;
        for (int t = 0; t < n; t++)
        {
            den += (rank[t] - centre) * (rank[t] - centre);
            if (t > 0)
                num += (rank[t] - rank[t - 1]) * (rank[t] - rank[t - 1]);
        }
        double ratio = num / den;
        double nd = n;
        double variance = 4 * (nd - 2) * (5 * nd * nd - 2 * nd - 9) / (5 * nd * (nd + 1) * (nd - 1) * (nd - 1));
        return new BartelsRankTest(ratio, (ratio - 2) / Math.Sqrt(variance));
    }
}
