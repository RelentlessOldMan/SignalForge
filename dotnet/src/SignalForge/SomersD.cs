namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Somers' D, d_yx: concordant less discordant pairs over the pairs untied in
    /// <paramref name="x"/>, for predicting <paramref name="y"/> from it (conventions: Somers'
    /// D; ADR 0378).</summary>
    /// <param name="x">Real samples, finite.</param>
    /// <param name="y">Real samples, finite, as many as <paramref name="x"/>.</param>
    /// <returns>D, from −1 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or no pair is untied
    /// in x.</exception>
    public static double SomersD(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
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
        long concordant = 0, discordant = 0, untied = 0;
        for (int i = 0; i < n; i++)
        {
            for (int j = i + 1; j < n; j++)
            {
                int cx = x[i].CompareTo(x[j]);
                if (cx != 0)
                    untied++;
                int p = cx * y[i].CompareTo(y[j]);
                if (p > 0)
                    concordant++;
                else if (p < 0)
                    discordant++;
            }
        }
        if (untied == 0)
            throw new ArgumentException("no pair is untied in x", nameof(x));
        return (double)(concordant - discordant) / untied;
    }
}
