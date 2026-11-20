namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Hamming distance between the real vectors <paramref name="x"/> and
    /// <paramref name="y"/>: the number of indices where they differ (conventions: Hamming
    /// distance; ADR 0421).</summary>
    /// <param name="x">The first vector, finite.</param>
    /// <param name="y">The second vector, finite and the same length as x.</param>
    /// <returns>The count, from 0 to the length.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static int HammingDistance(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        CliffCheck(x, nameof(x));
        CliffCheck(y, nameof(y));
        if (x.Length != y.Length)
            throw new ArgumentException("x and y must have the same length", nameof(y));
        int n = 0;
        for (int i = 0; i < x.Length; i++)
        {
            if (x[i] != y[i])
                n++;
        }
        return n;
    }
}
