namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Pearson product-moment correlation of <paramref name="x"/> and
    /// <paramref name="y"/> (conventions: Pearson correlation; ADR 0371).</summary>
    /// <param name="x">Real samples, finite, at least 2 and not all equal.</param>
    /// <param name="y">Real samples, finite, as many as <paramref name="x"/> and not all
    /// equal.</param>
    /// <returns>The correlation, from −1 to 1 up to rounding.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double PearsonCorrelation(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        int n = x.Length;
        if (y.Length != n)
            throw new ArgumentException("x and y must be the same length", nameof(y));
        if (n < 2)
            throw new ArgumentException("x and y must have at least 2 values", nameof(x));
        double sx = 0, sy = 0;
        for (int i = 0; i < n; i++)
        {
            if (!double.IsFinite(x[i]))
                throw new ArgumentException("x must be finite", nameof(x));
            if (!double.IsFinite(y[i]))
                throw new ArgumentException("y must be finite", nameof(y));
            sx += x[i];
            sy += y[i];
        }
        double mx = sx / n, my = sy / n, xy = 0, xx = 0, yy = 0;
        bool xConst = true, yConst = true;
        for (int i = 0; i < n; i++)
        {
            xConst &= x[i] == x[0];
            yConst &= y[i] == y[0];
            double u = x[i] - mx, w = y[i] - my;
            xy += u * w;
            xx += u * u;
            yy += w * w;
        }
        if (xConst || yConst)
            throw new ArgumentException("neither x nor y may have every value equal", xConst ? nameof(x) : nameof(y));
        return xy / Math.Sqrt(xx * yy);
    }
}
