namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The proportional similarity of the records <paramref name="x"/> and
    /// <paramref name="y"/> of values at least 0, each with a value above 0: sum(min(p, q))
    /// over their shares, from 0 to 1 (conventions: proportional similarity; ADR
    /// 0572).</summary>
    /// <param name="x">The first record, finite, at least 0, with a value above 0.</param>
    /// <param name="y">The second record, finite, at least 0, with a value above 0, the same
    /// length as x.</param>
    /// <returns>The similarity, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double CzekanowskiSimilarity(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
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
        double acc = 0;
        for (int i = 0; i < x.Length; i++)
            acc += Math.Min(x[i] / mx / tx, y[i] / my / ty);
        return Math.Min(acc, 1.0);
    }
}
