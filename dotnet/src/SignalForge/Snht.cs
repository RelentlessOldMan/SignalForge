namespace SignalForge;

/// <summary>The standard normal homogeneity statistic and the last sample before the change
/// (conventions: Standard normal homogeneity test; ADR 0368).</summary>
/// <param name="Statistic">The largest <c>T_k</c> over the splits.</param>
/// <param name="Index"><c>k − 1</c> for the smallest <c>k</c> reaching it: the last sample
/// before the change.</param>
public sealed record Snht(double Statistic, int Index);

public static partial class Measurements
{
    /// <summary>Alexandersson's standard normal homogeneity test: the largest <c>T_k</c> over
    /// the splits, and the last sample before the change (conventions: Standard normal
    /// homogeneity test; ADR 0368).</summary>
    /// <param name="samples">Real samples, finite, at least 2 and not all equal.</param>
    /// <returns>The statistic and its location.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Snht Snht(ReadOnlySpan<double> samples)
    {
        int n = samples.Length;
        if (n < 2)
            throw new ArgumentException("samples must have at least 2 values", nameof(samples));
        samples = ScaledByPowerOf2(samples);
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
        double s = 0, best = double.NegativeInfinity;
        int index = 0;
        for (int k = 1; k < n; k++)
        {
            s += samples[k - 1] - mean;
            double t = n * s * s / (k * (double)(n - k) * variance);
            if (t > best)
            {
                best = t;
                index = k - 1;
            }
        }
        return new Snht(best, index);
    }
}
