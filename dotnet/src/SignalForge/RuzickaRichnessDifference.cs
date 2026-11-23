namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The richness-difference part of the Ruzicka dissimilarity of the records
    /// <paramref name="x"/> and <paramref name="y"/> of values at least 0, each with a value
    /// above 0: |B - C|/(A + B + C), from 0 to 1 (conventions: richness-difference part of
    /// the Ruzicka dissimilarity; ADR 0587).</summary>
    /// <param name="x">The first record, finite, at least 0, with a value above 0.</param>
    /// <param name="y">The second record, finite, at least 0, with a value above 0, the same
    /// length as x.</param>
    /// <returns>The richness-difference part, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double RuzickaRichnessDifference(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        double m = Math.Max(PiankaTop(x, nameof(x)), PiankaTop(y, nameof(y)));
        if (x.Length != y.Length)
            throw new ArgumentException("x and y must have the same length", nameof(y));
        double shared = 0, onlyX = 0, onlyY = 0;
        for (int i = 0; i < x.Length; i++)
        {
            double lo = Math.Min(x[i], y[i]);
            shared += lo / m;
            onlyX += (x[i] - lo) / m;
            onlyY += (y[i] - lo) / m;
        }
        return Math.Abs(onlyX - onlyY) / (shared + (onlyX + onlyY));
    }
}
