namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Glass's delta: the difference of the means of the treated sample
    /// <paramref name="x"/> and the control <paramref name="y"/> over the control's sample
    /// standard deviation (conventions: Glass's delta; ADR 0399).</summary>
    /// <param name="x">The treated sample, finite; at least 1 value.</param>
    /// <param name="y">The control sample, finite; at least 2 values.</param>
    /// <returns>The effect size.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or the control's
    /// standard deviation is zero.</exception>
    public static double GlassDelta(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        if (x.Length < 1)
            throw new ArgumentException("x must hold at least 1 values", nameof(x));
        if (y.Length < 2)
            throw new ArgumentException("y must hold at least 2 values", nameof(y));
        double mx = GlassMean(x, nameof(x));
        double my = GlassMean(y, nameof(y));
        double ss = 0;
        foreach (double v in y)
            ss += (v - my) * (v - my);
        double s = Math.Sqrt(ss / (y.Length - 1));
        if (s == 0)
            throw new ArgumentException("the control's standard deviation is zero", nameof(y));
        return (mx - my) / s;
    }

    static double GlassMean(ReadOnlySpan<double> values, string name)
    {
        double total = 0;
        foreach (double v in values)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException($"{name} must be finite", name);
            total += v;
        }
        return total / values.Length;
    }
}
