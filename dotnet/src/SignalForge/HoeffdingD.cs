namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Hoeffding's D: a rank statistic of dependence of any shape, 1 for a monotone
    /// pair without ties and about 0 for independent ones (conventions: Hoeffding's D;
    /// ADR 0374).</summary>
    /// <param name="x">Real samples, finite, at least 5.</param>
    /// <param name="y">Real samples, finite, as many as <paramref name="x"/>.</param>
    /// <returns>D, from −1/2 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double HoeffdingD(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        int n = x.Length;
        if (y.Length != n)
            throw new ArgumentException("x and y must be the same length", nameof(y));
        if (n < 5)
            throw new ArgumentException("x and y must have at least 5 values", nameof(x));
        for (int i = 0; i < n; i++)
        {
            if (!double.IsFinite(x[i]))
                throw new ArgumentException("x must be finite", nameof(x));
            if (!double.IsFinite(y[i]))
                throw new ArgumentException("y must be finite", nameof(y));
        }
        double[] r = HoeffdingRanks(x), s = HoeffdingRanks(y);
        double d1 = 0, d2 = 0, d3 = 0;
        for (int i = 0; i < n; i++)
        {
            double q = 1;
            for (int j = 0; j < n; j++)
            {
                if (j != i)
                    q += Phi(x[j], x[i]) * Phi(y[j], y[i]);
            }
            d1 += (q - 1) * (q - 2);
            d2 += (r[i] - 1) * (r[i] - 2) * (s[i] - 1) * (s[i] - 2);
            d3 += (r[i] - 2) * (s[i] - 2) * (q - 1);
        }
        double nf = n;
        double top = (nf - 2) * (nf - 3) * d1 + d2 - 2 * (nf - 2) * d3;
        return 30 * top / (nf * (nf - 1) * (nf - 2) * (nf - 3) * (nf - 4));

        static double Phi(double a, double b) => a < b ? 1 : a == b ? 0.5 : 0;
    }

    static double[] HoeffdingRanks(ReadOnlySpan<double> samples)
    {
        int n = samples.Length;
        var order = new int[n];
        for (int i = 0; i < n; i++)
            order[i] = i;
        var keys = samples.ToArray();
        Array.Sort(keys, order);
        var rank = new double[n];
        for (int i = 0; i < n;)
        {
            int j = i;
            while (j + 1 < n && keys[j + 1] == keys[i])
                j++;
            double mean = (i + j) / 2.0 + 1;
            for (int k = i; k <= j; k++)
                rank[order[k]] = mean;
            i = j + 1;
        }
        return rank;
    }
}
