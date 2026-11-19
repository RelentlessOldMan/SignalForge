namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Chebyshev distance between the real vectors <paramref name="x"/> and
    /// <paramref name="y"/>: their largest coordinate difference (conventions: Chebyshev
    /// distance; ADR 0420).</summary>
    /// <param name="x">The first vector, finite.</param>
    /// <param name="y">The second vector, finite and the same length as x.</param>
    /// <returns>The distance, zero or more.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double ChebyshevDistance(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        CliffCheck(x, nameof(x));
        CliffCheck(y, nameof(y));
        if (x.Length != y.Length)
            throw new ArgumentException("x and y must have the same length", nameof(y));
        double m = 0;
        for (int i = 0; i < x.Length; i++)
        {
            double d = Math.Abs(x[i] - y[i]);
            if (double.IsInfinity(d))
                throw new ArgumentException("a difference of x and y overflows", nameof(y));
            if (d > m)
                m = d;
        }
        return m;
    }
}
