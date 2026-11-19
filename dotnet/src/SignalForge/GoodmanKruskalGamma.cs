namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Goodman and Kruskal's gamma: concordant less discordant pairs over their sum,
    /// pairs tied in either record dropped (conventions: Goodman and Kruskal's gamma;
    /// ADR 0377).</summary>
    /// <param name="x">Real samples, finite.</param>
    /// <param name="y">Real samples, finite, as many as <paramref name="x"/>.</param>
    /// <returns>Gamma, from −1 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or no pair is untied
    /// in both records.</exception>
    public static double GoodmanKruskalGamma(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        int n = x.Length;
        if (y.Length != n)
            throw new ArgumentException("x and y must be the same length", nameof(y));
        for (int i = 0; i < n; i++)
        {
            if (!double.IsFinite(x[i]))
                throw new ArgumentException("x must be finite", nameof(x));
            if (!double.IsFinite(y[i]))
                throw new ArgumentException("y must be finite", nameof(y));
        }
        long concordant = 0, discordant = 0;
        for (int i = 0; i < n; i++)
        {
            for (int j = i + 1; j < n; j++)
            {
                int p = x[i].CompareTo(x[j]) * y[i].CompareTo(y[j]);
                if (p > 0)
                    concordant++;
                else if (p < 0)
                    discordant++;
            }
        }
        if (concordant + discordant == 0)
            throw new ArgumentException("no pair is untied in both x and y", nameof(x));
        return (double)(concordant - discordant) / (concordant + discordant);
    }
}
