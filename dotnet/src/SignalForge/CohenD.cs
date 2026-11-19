namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Cohen's d: the difference of the means of <paramref name="x"/> and
    /// <paramref name="y"/> over their pooled standard deviation, positive when
    /// <paramref name="x"/> has the larger mean (conventions: Cohen's d; ADR 0397).</summary>
    /// <param name="x">The first sample, finite; at least 2 values.</param>
    /// <param name="y">The second sample, finite; at least 2 values.</param>
    /// <returns>The effect size.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or the pooled standard
    /// deviation is zero.</exception>
    public static double CohenD(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        double ss = 0;
        double mx = CohenDMean(x, nameof(x), ref ss);
        double my = CohenDMean(y, nameof(y), ref ss);
        double s = Math.Sqrt(ss / (x.Length + y.Length - 2));
        if (s == 0)
            throw new ArgumentException("the pooled standard deviation is zero", nameof(y));
        return (mx - my) / s;
    }

    static double CohenDMean(ReadOnlySpan<double> values, string name, ref double ss)
    {
        if (values.Length < 2)
            throw new ArgumentException($"{name} must hold at least 2 values", name);
        double total = 0;
        foreach (double v in values)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException($"{name} must be finite", name);
            total += v;
        }
        double mean = total / values.Length;
        foreach (double v in values)
            ss += (v - mean) * (v - mean);
        return mean;
    }
}
