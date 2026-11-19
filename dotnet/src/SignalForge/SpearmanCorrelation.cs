namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Spearman's rank correlation: the Pearson correlation of the ranks of
    /// <paramref name="x"/> and <paramref name="y"/>, ties given their mean rank (conventions:
    /// Spearman rank correlation; ADR 0369).</summary>
    /// <param name="x">Real samples, finite, at least 2 and not all equal.</param>
    /// <param name="y">Real samples, finite, as many as <paramref name="x"/> and not all
    /// equal.</param>
    /// <returns>The rank correlation, from −1 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double SpearmanCorrelation(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        foreach (double v in x)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("x must be finite", nameof(x));
        }
        foreach (double v in y)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("y must be finite", nameof(y));
        }
        int n = x.Length;
        if (y.Length != n)
            throw new ArgumentException("x and y must be the same length", nameof(y));
        if (n < 2)
            throw new ArgumentException("x and y must have at least 2 values", nameof(x));
        double[] r = SpearmanRanks(x, nameof(x)), s = SpearmanRanks(y, nameof(y));
        double c = (n + 1) / 2.0, rs = 0, rr = 0, ss = 0;
        for (int i = 0; i < n; i++)
        {
            double u = r[i] - c, w = s[i] - c;
            rs += u * w;
            rr += u * u;
            ss += w * w;
        }
        return rs / Math.Sqrt(rr * ss);
    }

    static double[] SpearmanRanks(ReadOnlySpan<double> samples, string name)
    {
        int n = samples.Length;
        var order = new int[n];
        for (int i = 0; i < n; i++)
            order[i] = i;
        var keys = samples.ToArray();
        Array.Sort(keys, order);
        if (keys[0] == keys[n - 1])
            throw new ArgumentException("neither x nor y may have every value equal", name);
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
