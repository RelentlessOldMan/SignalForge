namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Fisher's alpha of a record of whole numbers at least 0 totalling more than
    /// the count of values above 0: the log-series alpha with k = alpha ln(1 + N/alpha)
    /// (conventions: Fisher's alpha; ADR 0550).</summary>
    /// <param name="samples">Whole numbers at least 0, totalling more than the count of
    /// values above 0 and at most 10 000 000.</param>
    /// <returns>Fisher's alpha, above 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double FisherAlpha(ReadOnlySpan<double> samples)
    {
        int n = samples.Length;
        if (n < 1)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        double total = 0;
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            if (v < 0)
                throw new ArgumentException("samples must be at least 0", nameof(samples));
            if (v != Math.Floor(v))
                throw new ArgumentException("samples must be whole numbers", nameof(samples));
            total += v;
        }
        if (!(total > 0))
            throw new ArgumentException("samples must not all be 0", nameof(samples));
        if (total > 10_000_000)
            throw new ArgumentException("samples must total at most 10 000 000", nameof(samples));
        int k = 0;
        foreach (double v in samples)
        {
            if (v > 0)
                k++;
        }
        if (!(k < total))
            throw new ArgumentException("samples must total more than the count of values above 0", nameof(samples));
        double lo = 1.0;
        while (Count(lo, total) >= k)
            lo /= 2.0;
        double hi = 1.0;
        while (Count(hi, total) <= k)
            hi *= 2.0;
        for (int step = 0; step < 100; step++)
        {
            double mid = Math.Sqrt(lo) * Math.Sqrt(hi);
            if (Count(mid, total) < k)
                lo = mid;
            else
                hi = mid;
        }
        return Math.Sqrt(lo) * Math.Sqrt(hi);

        static double Count(double alpha, double total)
        {
            double x = total / alpha;
            double u = 1.0 + x;
            double lp = u == 1.0 ? x : Math.Log(u) * x / (u - 1.0);
            return alpha * lp;
        }
    }
}
