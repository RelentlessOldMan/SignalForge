namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The energy distance between the samples <paramref name="x"/> and
    /// <paramref name="y"/>: twice the mean absolute difference between them less the mean
    /// within each, the squared form (conventions: energy distance; ADR 0404).</summary>
    /// <param name="x">The first sample, finite; at least 1 value.</param>
    /// <param name="y">The second sample, finite; at least 1 value.</param>
    /// <returns>The distance, zero or more, in the units of the samples.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double EnergyDistance(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        CliffCheck(x, nameof(x));
        CliffCheck(y, nameof(y));
        double e = 2.0 * EnergyMeanGap(x, y) - EnergyMeanGap(x, x) - EnergyMeanGap(y, y);
        return Math.Max(e, 0.0);
    }

    static double EnergyMeanGap(ReadOnlySpan<double> p, ReadOnlySpan<double> q)
    {
        double total = 0;
        foreach (double u in p)
        {
            foreach (double v in q)
                total += Math.Abs(u - v);
        }
        return total / ((double)p.Length * q.Length);
    }
}
