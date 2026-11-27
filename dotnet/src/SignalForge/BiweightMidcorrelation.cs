namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The biweight midcorrelation of <paramref name="x"/> and <paramref name="y"/>:
    /// a correlation of the deviations from the medians, weighted by Tukey's biweight in units
    /// of <c>9 MAD</c> (conventions: Biweight midcorrelation; ADR 0373).</summary>
    /// <param name="x">Real samples, finite, at least 2, with a nonzero median absolute
    /// deviation.</param>
    /// <param name="y">Real samples, finite, as many as <paramref name="x"/>, with a nonzero
    /// median absolute deviation.</param>
    /// <returns>The midcorrelation, from −1 to 1 up to rounding.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double BiweightMidcorrelation(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        x = ScaledToLargestMagnitude(x);
        y = ScaledToLargestMagnitude(y);
        int n = x.Length;
        if (y.Length != n)
            throw new ArgumentException("x and y must be the same length", nameof(y));
        if (n < 2)
            throw new ArgumentException("x and y must have at least 2 values", nameof(x));
        for (int i = 0; i < n; i++)
        {
            if (!double.IsFinite(x[i]))
                throw new ArgumentException("x must be finite", nameof(x));
            if (!double.IsFinite(y[i]))
                throw new ArgumentException("y must be finite", nameof(y));
        }
        double[] p = BiweightTerms(x, nameof(x)), q = BiweightTerms(y, nameof(y));
        double pq = 0, pp = 0, qq = 0;
        for (int i = 0; i < n; i++)
        {
            pq += p[i] * q[i];
            pp += p[i] * p[i];
            qq += q[i] * q[i];
        }
        return pq / Math.Sqrt(pp * qq);
    }

    static double[] BiweightTerms(ReadOnlySpan<double> v, string name)
    {
        int n = v.Length;
        double m = SortedMedian(v.ToArray());
        var d = new double[n];
        var ad = new double[n];
        for (int i = 0; i < n; i++)
        {
            d[i] = v[i] - m;
            ad[i] = Math.Abs(d[i]);
        }
        double mad = SortedMedian(ad);
        if (!(mad > 0))
            throw new ArgumentException($"{name} must have a nonzero median absolute deviation", name);
        double scale = 9 * mad;
        for (int i = 0; i < n; i++)
        {
            double u = d[i] / scale;
            d[i] = Math.Abs(u) < 1 ? d[i] * ((1 - u * u) * (1 - u * u)) : 0;
        }
        return d;
    }

    static double SortedMedian(double[] values)
    {
        Array.Sort(values);
        int k = values.Length;
        return k % 2 == 1 ? values[k / 2] : (values[k / 2 - 1] + values[k / 2]) / 2;
    }
}
