namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The nestedness part of the Sorensen dissimilarity of the records
    /// <paramref name="x"/> and <paramref name="y"/> of values at least 0, each with a value
    /// above 0: WhittakerBeta - SimpsonBeta, from 0 to 1 (conventions: nestedness part of the
    /// Sorensen dissimilarity; ADR 0577).</summary>
    /// <param name="x">The first record, finite, at least 0, with a value above 0.</param>
    /// <param name="y">The second record, finite, at least 0, with a value above 0, the same
    /// length as x.</param>
    /// <returns>The nestedness part, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double NestednessBeta(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        PiankaTop(x, nameof(x));
        PiankaTop(y, nameof(y));
        if (x.Length != y.Length)
            throw new ArgumentException("x and y must have the same length", nameof(y));
        int both = 0, onlyX = 0, onlyY = 0;
        for (int i = 0; i < x.Length; i++)
        {
            if (x[i] > 0 && y[i] > 0)
                both++;
            else if (x[i] > 0)
                onlyX++;
            else if (y[i] > 0)
                onlyY++;
        }
        long least = Math.Min(onlyX, onlyY);
        long num = (long)Math.Abs(onlyX - onlyY) * both;
        return (double)num / ((2L * both + onlyX + onlyY) * (both + least));
    }
}
