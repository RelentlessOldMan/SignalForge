namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Chatterjee's xi: how well <paramref name="x"/> predicts <paramref name="y"/>,
    /// near 0 for independent records and near 1 when y is a function of x (conventions:
    /// Chatterjee's xi; ADR 0376).</summary>
    /// <param name="x">Real samples, finite, at least 2.</param>
    /// <param name="y">Real samples, finite, not all equal, as many as
    /// <paramref name="x"/>.</param>
    /// <returns>Xi, at most 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double ChatterjeeXi(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
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
        var xs = x.ToArray();
        var order = new int[n];
        for (int i = 0; i < n; i++)
            order[i] = i;
        // Ties in x keep their record order.
        Array.Sort(order, (p, q) => xs[p] != xs[q] ? xs[p].CompareTo(xs[q]) : p.CompareTo(q));
        var sy = y.ToArray();
        Array.Sort(sy);
        long s = 0, t = 0, previous = 0;
        for (int i = 0; i < n; i++)
        {
            double v = y[order[i]];
            long r = Bound(sy, v, true);
            long l = n - Bound(sy, v, false);
            if (i > 0)
                s += Math.Abs(r - previous);
            previous = r;
            t += l * (n - l);
        }
        if (t == 0)
            throw new ArgumentException("y must not be constant", nameof(y));
        return 1 - (double)(n * s) / (2 * t);

        // The number of sorted values below v, or at most v when upper is set.
        static int Bound(double[] sorted, double v, bool upper)
        {
            int lo = 0, hi = sorted.Length;
            while (lo < hi)
            {
                int mid = (lo + hi) >>> 1;
                if (sorted[mid] < v || (upper && sorted[mid] == v))
                    lo = mid + 1;
                else
                    hi = mid;
            }
            return lo;
        }
    }
}
