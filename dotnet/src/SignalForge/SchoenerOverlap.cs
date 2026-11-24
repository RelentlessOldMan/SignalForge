namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Schoener's overlap of the records <paramref name="x"/> and
    /// <paramref name="y"/> of values at least 0, each with a value above 0: sum(min(p, q))
    /// on their shares, from 0 to 1 (conventions: Schoener's overlap; ADR 0598).</summary>
    /// <param name="x">The first record, finite, at least 0, with a value above 0.</param>
    /// <param name="y">The second record, finite, at least 0, with a value above 0, the same
    /// length as x.</param>
    /// <returns>Schoener's overlap, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double SchoenerOverlap(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        double topX = PiankaTop(x, nameof(x));
        double topY = PiankaTop(y, nameof(y));
        if (x.Length != y.Length)
            throw new ArgumentException("x and y must have the same length", nameof(y));
        double sx = 0, sy = 0;
        for (int i = 0; i < x.Length; i++)
        {
            sx += x[i] / topX;
            sy += y[i] / topY;
        }
        double total = 0;
        for (int i = 0; i < x.Length; i++)
            total += Math.Min(x[i] / topX / sx, y[i] / topY / sy);
        return Math.Min(total, 1.0);
    }
}
