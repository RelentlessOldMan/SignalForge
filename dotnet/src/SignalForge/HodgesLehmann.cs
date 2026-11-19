namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Hodges–Lehmann shift estimate: the median of every difference between a
    /// value of <paramref name="x"/> and a value of <paramref name="y"/> (conventions:
    /// Hodges–Lehmann shift estimate; ADR 0406).</summary>
    /// <param name="x">The first sample, finite; at least 1 value.</param>
    /// <param name="y">The second sample, finite; at least 1 value.</param>
    /// <returns>The estimated shift of x from y, in the units of the samples.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double HodgesLehmann(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        CliffCheck(x, nameof(x));
        CliffCheck(y, nameof(y));
        var d = new double[(long)x.Length * y.Length];
        int k = 0;
        foreach (double u in x)
        {
            foreach (double v in y)
                d[k++] = u - v;
        }
        Array.Sort(d);
        int m = d.Length;
        return m % 2 == 1 ? d[m / 2] : (d[m / 2 - 1] + d[m / 2]) / 2.0;
    }
}
