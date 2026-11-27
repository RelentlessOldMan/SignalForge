namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Ljung–Box statistic <c>N(N+2) Σ ρ_k²/(N−k)</c> over lags 1 to
    /// <paramref name="lags"/> (conventions: Ljung–Box statistic; ADR 0359).</summary>
    /// <param name="samples">Real samples, finite and not all equal.</param>
    /// <param name="lags">The number of lags, from 1 to <c>samples.Length − 1</c>.</param>
    /// <returns>The statistic <c>Q</c>.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double LjungBox(ReadOnlySpan<double> samples, int lags)
    {
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        samples = ScaledByPowerOf2(samples);
        double sum = 0;
        foreach (double v in samples)
            sum += v;
        int n = samples.Length;
        if (lags < 1 || lags > n - 1)
            throw new ArgumentOutOfRangeException(nameof(lags), lags, "must be from 1 to samples.Length - 1");
        double mean = sum / n;
        var d = new double[n];
        double c0 = 0;
        for (int t = 0; t < n; t++)
        {
            d[t] = samples[t] - mean;
            c0 += d[t] * d[t];
        }
        if (!(c0 > 0))
            throw new ArgumentException("samples must not all be equal", nameof(samples));
        double q = 0;
        for (int k = 1; k <= lags; k++)
        {
            double c = 0;
            for (int t = 0; t < n - k; t++)
                c += d[t] * d[t + k];
            double rho = c / c0;
            q += rho * rho / (n - k);
        }
        return (double)n * (n + 2) * q;
    }
}
