namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The two-sample Kolmogorov–Smirnov statistic: the largest gap between the
    /// empirical distribution functions of <paramref name="x"/> and <paramref name="y"/>
    /// (conventions: two-sample Kolmogorov–Smirnov statistic; ADR 0402).</summary>
    /// <param name="x">The first sample, finite; at least 1 value.</param>
    /// <param name="y">The second sample, finite; at least 1 value.</param>
    /// <returns>The statistic, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double KolmogorovSmirnov(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        CliffCheck(x, nameof(x));
        CliffCheck(y, nameof(y));
        var xs = x.ToArray();
        var ys = y.ToArray();
        Array.Sort(xs);
        Array.Sort(ys);
        long nx = xs.Length, ny = ys.Length, gap = 0;
        int i = 0, j = 0;
        while (i < xs.Length || j < ys.Length)
        {
            double t = j == ys.Length || (i < xs.Length && xs[i] <= ys[j]) ? xs[i] : ys[j];
            while (i < xs.Length && xs[i] <= t)
                i++;
            while (j < ys.Length && ys[j] <= t)
                j++;
            gap = Math.Max(gap, Math.Abs(i * ny - j * nx));
        }
        return (double)gap / (nx * ny);
    }
}
