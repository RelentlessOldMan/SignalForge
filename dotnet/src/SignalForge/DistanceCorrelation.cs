namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The distance correlation of <paramref name="x"/> and <paramref name="y"/>,
    /// from the double-centred distance matrices, 0 only for independent records (conventions:
    /// Distance correlation; ADR 0372).</summary>
    /// <param name="x">Real samples, finite, at least 2 and not all equal.</param>
    /// <param name="y">Real samples, finite, as many as <paramref name="x"/> and not all
    /// equal.</param>
    /// <returns>The distance correlation, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double DistanceCorrelation(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        x = ScaledToLargestMagnitude(x);
        y = ScaledToLargestMagnitude(y);
        int n = x.Length;
        if (y.Length != n)
            throw new ArgumentException("x and y must be the same length", nameof(y));
        if (n < 2)
            throw new ArgumentException("x and y must have at least 2 values", nameof(x));
        bool xConst = true, yConst = true;
        for (int i = 0; i < n; i++)
        {
            if (!double.IsFinite(x[i]))
                throw new ArgumentException("x must be finite", nameof(x));
            if (!double.IsFinite(y[i]))
                throw new ArgumentException("y must be finite", nameof(y));
            xConst &= x[i] == x[0];
            yConst &= y[i] == y[0];
        }
        if (xConst || yConst)
            throw new ArgumentException("neither x nor y may have every value equal", xConst ? nameof(x) : nameof(y));
        double[,] a = DoubleCentred(x), b = DoubleCentred(y);
        double ab = 0, aa = 0, bb = 0;
        for (int i = 0; i < n; i++)
        {
            for (int j = 0; j < n; j++)
            {
                ab += a[i, j] * b[i, j];
                aa += a[i, j] * a[i, j];
                bb += b[i, j] * b[i, j];
            }
        }
        double nn = (double)n * n;
        double cov = ab / nn, va = aa / nn, vb = bb / nn;
        return Math.Sqrt(Math.Max(0, cov) / Math.Sqrt(va * vb));
    }

    static double[,] DoubleCentred(ReadOnlySpan<double> v)
    {
        int n = v.Length;
        var a = new double[n, n];
        var m = new double[n];
        for (int i = 0; i < n; i++)
        {
            double s = 0;
            for (int j = 0; j < n; j++)
            {
                a[i, j] = Math.Abs(v[i] - v[j]);
                s += a[i, j];
            }
            m[i] = s / n;
        }
        double g = 0;
        foreach (double r in m)
            g += r;
        g /= n;
        for (int i = 0; i < n; i++)
        {
            for (int j = 0; j < n; j++)
                a[i, j] = a[i, j] - m[i] - m[j] + g;
        }
        return a;
    }
}
