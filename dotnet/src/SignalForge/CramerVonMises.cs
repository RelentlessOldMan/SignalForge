namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The two-sample Cramér–von Mises statistic: the scaled sum of the squared gaps
    /// between the empirical distribution functions of <paramref name="x"/> and
    /// <paramref name="y"/> over the pooled sample (conventions: two-sample Cramér–von Mises
    /// statistic; ADR 0405).</summary>
    /// <param name="x">The first sample, finite; at least 1 value.</param>
    /// <param name="y">The second sample, finite; at least 1 value.</param>
    /// <returns>The statistic, zero or more.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double CramerVonMises(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        CliffCheck(x, nameof(x));
        CliffCheck(y, nameof(y));
        var xs = x.ToArray();
        var ys = y.ToArray();
        Array.Sort(xs);
        Array.Sort(ys);
        long nx = xs.Length, ny = ys.Length;
        int i = 0, j = 0;
        double total = 0;
        while (i < xs.Length || j < ys.Length)
        {
            double t = j == ys.Length || (i < xs.Length && xs[i] <= ys[j]) ? xs[i] : ys[j];
            int before = i + j;
            while (i < xs.Length && xs[i] <= t)
                i++;
            while (j < ys.Length && ys[j] <= t)
                j++;
            double g = Math.Abs(i * ny - j * nx);
            total += (double)(i + j - before) * (g * g);
        }
        double n = nx + ny;
        return total / ((double)nx * ny * n * n);
    }
}
