namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Pianka's niche overlap of the records <paramref name="x"/> and
    /// <paramref name="y"/> of values at least 0, each with a value above 0:
    /// sum(p q)/sqrt(sum(p^2) sum(q^2)) on their shares, from 0 to 1 (conventions: Pianka's
    /// niche overlap; ADR 0571).</summary>
    /// <param name="x">The first record, finite, at least 0, with a value above 0.</param>
    /// <param name="y">The second record, finite, at least 0, with a value above 0, the same
    /// length as x.</param>
    /// <returns>The overlap, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double PiankaOverlap(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        double mx = PiankaTop(x, nameof(x));
        double my = PiankaTop(y, nameof(y));
        if (x.Length != y.Length)
            throw new ArgumentException("x and y must have the same length", nameof(y));
        double sxy = 0, sxx = 0, syy = 0;
        for (int i = 0; i < x.Length; i++)
        {
            double a = x[i] / mx;
            double b = y[i] / my;
            sxy += a * b;
            sxx += a * a;
            syy += b * b;
        }
        return Math.Min(sxy / Math.Sqrt(sxx * syy), 1.0);
    }

    // The largest value of a record checked as Pianka's overlap requires.
    static double PiankaTop(ReadOnlySpan<double> values, string name)
    {
        CliffCheck(values, name);
        double top = 0;
        foreach (double v in values)
        {
            if (v < 0)
                throw new ArgumentException($"{name} must be at least 0", name);
            top = Math.Max(top, v);
        }
        if (!(top > 0))
            throw new ArgumentException($"{name} must have a value above 0", name);
        return top;
    }
}
