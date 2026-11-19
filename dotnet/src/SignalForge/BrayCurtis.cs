namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Bray–Curtis dissimilarity between the non-negative vectors
    /// <paramref name="x"/> and <paramref name="y"/>: the share of their combined total that
    /// does not match (conventions: Bray–Curtis dissimilarity; ADR 0418).</summary>
    /// <param name="x">The first vector, finite and non-negative.</param>
    /// <param name="y">The second vector, finite, non-negative and the same length as x;
    /// x and y not both all zero.</param>
    /// <returns>The dissimilarity, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double BrayCurtis(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        CliffCheck(x, nameof(x));
        CliffCheck(y, nameof(y));
        if (x.Length != y.Length)
            throw new ArgumentException("x and y must have the same length", nameof(y));
        double num = 0, den = 0;
        for (int i = 0; i < x.Length; i++)
        {
            if (x[i] < 0)
                throw new ArgumentException("x must be non-negative", nameof(x));
            if (y[i] < 0)
                throw new ArgumentException("y must be non-negative", nameof(y));
            num += Math.Abs(x[i] - y[i]);
            den += x[i] + y[i];
        }
        if (!(den > 0))
            throw new ArgumentException("x and y must not both be all zero", nameof(y));
        return Math.Min(num / den, 1.0);
    }
}
