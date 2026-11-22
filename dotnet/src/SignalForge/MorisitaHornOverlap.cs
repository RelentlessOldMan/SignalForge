namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Morisita-Horn overlap of the records <paramref name="x"/> and
    /// <paramref name="y"/> of values at least 0, each with a value above 0:
    /// 2 sum(p q)/(sum(p^2) + sum(q^2)) on their shares, from 0 to 1 (conventions:
    /// Morisita-Horn overlap; ADR 0573).</summary>
    /// <param name="x">The first record, finite, at least 0, with a value above 0.</param>
    /// <param name="y">The second record, finite, at least 0, with a value above 0, the same
    /// length as x.</param>
    /// <returns>The overlap, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double MorisitaHornOverlap(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        double mx = PiankaTop(x, nameof(x));
        double my = PiankaTop(y, nameof(y));
        if (x.Length != y.Length)
            throw new ArgumentException("x and y must have the same length", nameof(y));
        double tx = 0, ty = 0;
        for (int i = 0; i < x.Length; i++)
        {
            tx += x[i] / mx;
            ty += y[i] / my;
        }
        double sxy = 0, sxx = 0, syy = 0;
        for (int i = 0; i < x.Length; i++)
        {
            double a = x[i] / mx / tx;
            double b = y[i] / my / ty;
            sxy += a * b;
            sxx += a * a;
            syy += b * b;
        }
        return Math.Min(2.0 * sxy / (sxx + syy), 1.0);
    }
}
