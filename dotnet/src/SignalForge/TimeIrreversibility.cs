namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The skewness of the lag increments, <c>M3/(M2·√M2)</c>, a time-irreversibility
    /// statistic that is 0 on average for a reversible process (conventions: Time
    /// irreversibility; ADR 0357).</summary>
    /// <param name="samples">Real samples, finite.</param>
    /// <param name="lag">The increment lag, from 1 to <c>samples.Length − 1</c>.</param>
    /// <returns>The skewness of the increments.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or every increment is 0.</exception>
    public static double TimeIrreversibility(ReadOnlySpan<double> samples, int lag = 1)
    {
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        if (lag < 1 || lag > samples.Length - 1)
            throw new ArgumentOutOfRangeException(nameof(lag), lag, "must be from 1 to samples.Length - 1");
        int n = samples.Length - lag;
        double s2 = 0, s3 = 0;
        for (int t = 0; t < n; t++)
        {
            double d = samples[t + lag] - samples[t];
            s2 += d * d;
            s3 += d * d * d;
        }
        double m2 = s2 / n;
        if (!(m2 > 0))
            throw new ArgumentException("the increments must not all be 0", nameof(samples));
        return s3 / n / (m2 * Math.Sqrt(m2));
    }
}
