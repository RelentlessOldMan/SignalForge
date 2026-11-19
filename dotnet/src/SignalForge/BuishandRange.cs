namespace SignalForge;

/// <summary>Buishand's rescaled partial-sum maximum and range, and where the maximum is reached
/// (conventions: Buishand range test; ADR 0367).</summary>
/// <param name="Q">The largest <c>|S_k|</c> over the population standard deviation.</param>
/// <param name="R">The range of the partial sums, with 0 included, over the population
/// standard deviation.</param>
/// <param name="Index">The smallest <c>k</c> with the largest <c>|S_k|</c>: the last sample
/// before the change.</param>
public sealed record BuishandRange(double Q, double R, int Index);

public static partial class Measurements
{
    /// <summary>Buishand's range test: the partial sums of the deviations from the mean, their
    /// largest size and their range over the population standard deviation, and the last
    /// sample before the change (conventions: Buishand range test; ADR 0367).</summary>
    /// <param name="samples">Real samples, finite, at least 2 and not all equal.</param>
    /// <returns>The rescaled maximum, the rescaled range and the location.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static BuishandRange BuishandRange(ReadOnlySpan<double> samples)
    {
        int n = samples.Length;
        if (n < 2)
            throw new ArgumentException("samples must have at least 2 values", nameof(samples));
        double sum = 0;
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            sum += v;
        }
        double mean = sum / n, ss = 0;
        foreach (double v in samples)
            ss += (v - mean) * (v - mean);
        double variance = ss / n;
        if (!(variance > 0))
            throw new ArgumentException("samples must not all be equal", nameof(samples));
        double sigma = Math.Sqrt(variance);
        double s = 0, hi = 0, lo = 0, top = -1;
        int index = 0;
        for (int k = 0; k < n; k++)
        {
            s += samples[k] - mean;
            hi = Math.Max(hi, s);
            lo = Math.Min(lo, s);
            if (Math.Abs(s) > top)
            {
                top = Math.Abs(s);
                index = k;
            }
        }
        return new BuishandRange(top / sigma, (hi - lo) / sigma, index);
    }
}
