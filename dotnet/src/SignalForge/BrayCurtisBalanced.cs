namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The balanced-variation part of the Bray-Curtis dissimilarity of the records
    /// <paramref name="x"/> and <paramref name="y"/> of values at least 0, each with a value
    /// above 0: min(B, C)/(A + min(B, C)), from 0 to 1 (conventions: balanced-variation part
    /// of the Bray-Curtis dissimilarity; ADR 0582).</summary>
    /// <param name="x">The first record, finite, at least 0, with a value above 0.</param>
    /// <param name="y">The second record, finite, at least 0, with a value above 0, the same
    /// length as x.</param>
    /// <returns>The balanced-variation part, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double BrayCurtisBalanced(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
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
        double least = Math.Min(onlyX, onlyY);
        return least / (shared + least);
    }
}
