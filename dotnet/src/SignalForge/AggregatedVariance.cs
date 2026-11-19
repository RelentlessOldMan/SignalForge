namespace SignalForge;

/// <summary>The variance of the block means at each size and the Hurst exponent they give
/// (conventions: Aggregated variance; ADR 0355).</summary>
/// <param name="Sizes">The block sizes in samples, in the order given.</param>
/// <param name="Values">The population variance of the block means at each size.</param>
/// <param name="Hurst"><c>1 + β/2</c>, with <c>β</c> the least-squares slope of
/// <c>ln values</c> against <c>ln s</c>.</param>
public sealed record AggregatedVariance(int[] Sizes, double[] Values, double Hurst);

public static partial class Measurements
{
    /// <summary>The aggregated-variance Hurst estimator: the population variance of the means
    /// of non-overlapping blocks at each size, and <c>1 + slope/2</c> of its log-log line
    /// (conventions: Aggregated variance; ADR 0355).</summary>
    /// <param name="samples">Real samples, finite.</param>
    /// <param name="sizes">At least two block sizes, strictly increasing, each from 1 to half
    /// the number of samples.</param>
    /// <returns>The sizes, the variance at each, and the Hurst exponent.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or the block means do
    /// not vary at some size.</exception>
    public static AggregatedVariance AggregatedVariance(ReadOnlySpan<double> samples, ReadOnlySpan<int> sizes)
    {
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        if (sizes.Length < 2)
            throw new ArgumentException("sizes must have at least two entries", nameof(sizes));
        for (int i = 0; i < sizes.Length; i++)
        {
            if (sizes[i] < 1 || 2L * sizes[i] > samples.Length)
                throw new ArgumentException("each size must be at least 1 and at most samples.Length / 2", nameof(sizes));
            if (i > 0 && sizes[i] <= sizes[i - 1])
                throw new ArgumentException("sizes must be strictly increasing", nameof(sizes));
        }
        var values = new double[sizes.Length];
        for (int f = 0; f < sizes.Length; f++)
        {
            int s = sizes[f];
            int blocks = samples.Length / s;
            var means = new double[blocks];
            double grand = 0;
            for (int b = 0; b < blocks; b++)
            {
                double sum = 0;
                foreach (double v in samples.Slice(b * s, s))
                    sum += v;
                means[b] = sum / s;
                grand += means[b];
            }
            grand /= blocks;
            double squares = 0;
            foreach (double v in means)
                squares += (v - grand) * (v - grand);
            values[f] = squares / blocks;
            if (!(values[f] > 0))
                throw new ArgumentException("every size must have block means that vary", nameof(samples));
        }
        double mx = 0, my = 0;
        for (int f = 0; f < sizes.Length; f++)
        {
            mx += Math.Log(sizes[f]);
            my += Math.Log(values[f]);
        }
        mx /= sizes.Length;
        my /= sizes.Length;
        double sxy = 0, sxx = 0;
        for (int f = 0; f < sizes.Length; f++)
        {
            double dx = Math.Log(sizes[f]) - mx;
            sxy += dx * (Math.Log(values[f]) - my);
            sxx += dx * dx;
        }
        return new AggregatedVariance(sizes.ToArray(), values, 1 + (sxy / sxx / 2));
    }
}
