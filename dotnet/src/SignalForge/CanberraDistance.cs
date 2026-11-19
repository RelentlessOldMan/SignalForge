namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Canberra distance between the real vectors <paramref name="x"/> and
    /// <paramref name="y"/>: each coordinate's difference over the sum of their magnitudes,
    /// added (conventions: Canberra distance; ADR 0417).</summary>
    /// <param name="x">The first vector, finite.</param>
    /// <param name="y">The second vector, finite and the same length as x.</param>
    /// <returns>The distance, from 0 to the length.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double CanberraDistance(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        CliffCheck(x, nameof(x));
        CliffCheck(y, nameof(y));
        if (x.Length != y.Length)
            throw new ArgumentException("x and y must have the same length", nameof(y));
        double s = 0;
        for (int i = 0; i < x.Length; i++)
        {
            if (x[i] == 0 && y[i] == 0)
                continue;
            s += Math.Abs(x[i] - y[i]) / (Math.Abs(x[i]) + Math.Abs(y[i]));
        }
        return s;
    }
}
