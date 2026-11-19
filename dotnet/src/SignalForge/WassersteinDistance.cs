namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The first Wasserstein distance between the samples <paramref name="x"/> and
    /// <paramref name="y"/>: the area between their empirical distribution functions
    /// (conventions: first Wasserstein distance; ADR 0403).</summary>
    /// <param name="x">The first sample, finite; at least 1 value.</param>
    /// <param name="y">The second sample, finite; at least 1 value.</param>
    /// <returns>The distance, in the units of the samples.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double WassersteinDistance(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        CliffCheck(x, nameof(x));
        CliffCheck(y, nameof(y));
        var xs = x.ToArray();
        var ys = y.ToArray();
        Array.Sort(xs);
        Array.Sort(ys);
        long nx = xs.Length, ny = ys.Length;
        int i = 0, j = 0;
        double total = 0, previous = 0;
        long gap = 0;
        bool first = true;
        while (i < xs.Length || j < ys.Length)
        {
            double t = j == ys.Length || (i < xs.Length && xs[i] <= ys[j]) ? xs[i] : ys[j];
            if (!first)
                total += (double)gap * (t - previous);
            while (i < xs.Length && xs[i] <= t)
                i++;
            while (j < ys.Length && ys[j] <= t)
                j++;
            gap = Math.Abs(i * ny - j * nx);
            previous = t;
            first = false;
        }
        return total / (nx * ny);
    }
}
