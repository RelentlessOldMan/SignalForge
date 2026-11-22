namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Ruzicka similarity of the records <paramref name="x"/> and
    /// <paramref name="y"/> of values at least 0, each with a value above 0:
    /// sum(min(x, y))/sum(max(x, y)), from 0 to 1 (conventions: Ruzicka similarity of two
    /// records; ADR 0580).</summary>
    /// <param name="x">The first record, finite, at least 0, with a value above 0.</param>
    /// <param name="y">The second record, finite, at least 0, with a value above 0, the same
    /// length as x.</param>
    /// <returns>The similarity, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double RuzickaSimilarity(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        double m = Math.Max(PiankaTop(x, nameof(x)), PiankaTop(y, nameof(y)));
        if (x.Length != y.Length)
            throw new ArgumentException("x and y must have the same length", nameof(y));
        double low = 0, high = 0;
        for (int i = 0; i < x.Length; i++)
        {
            low += Math.Min(x[i], y[i]) / m;
            high += Math.Max(x[i], y[i]) / m;
        }
        return low / high;
    }
}
