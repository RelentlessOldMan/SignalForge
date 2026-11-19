namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The order-<paramref name="order"/> Minkowski distance between the real
    /// vectors <paramref name="x"/> and <paramref name="y"/>, scaled by the largest difference
    /// so it cannot overflow (conventions: Minkowski distance; ADR 0419).</summary>
    /// <param name="x">The first vector, finite.</param>
    /// <param name="y">The second vector, finite and the same length as x.</param>
    /// <param name="order">The order, finite and at least 1.</param>
    /// <returns>The distance, zero or more.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double MinkowskiDistance(ReadOnlySpan<double> x, ReadOnlySpan<double> y, double order)
    {
        if (!double.IsFinite(order) || !(order >= 1))
            throw new ArgumentOutOfRangeException(nameof(order), order, "must be finite and at least 1");
        CliffCheck(x, nameof(x));
        CliffCheck(y, nameof(y));
        if (x.Length != y.Length)
            throw new ArgumentException("x and y must have the same length", nameof(y));
        var diffs = new double[x.Length];
        double m = 0;
        for (int i = 0; i < x.Length; i++)
        {
            double d = Math.Abs(x[i] - y[i]);
            if (double.IsInfinity(d))
                throw new ArgumentException("a difference of x and y overflows", nameof(y));
            diffs[i] = d;
            if (d > m)
                m = d;
        }
        if (m == 0)
            return 0.0;
        double s = 0;
        foreach (double d in diffs)
            s += Math.Pow(d / m, order);
        return m * Math.Pow(s, 1.0 / order);
    }
}
