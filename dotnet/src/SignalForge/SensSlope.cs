namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Sen's slope: the median of the slopes <c>(x_j − x_i)/(j − i)</c> over every
    /// pair <c>i &lt; j</c>, per sample (conventions: Sen's slope; ADR 0365).</summary>
    /// <param name="samples">Real samples, finite, at least 2.</param>
    /// <returns>The median pairwise slope.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double SensSlope(ReadOnlySpan<double> samples)
    {
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        int n = samples.Length;
        if (n < 2)
            throw new ArgumentException("samples must have at least 2 values", nameof(samples));
        var slopes = new double[(long)n * (n - 1) / 2];
        int k = 0;
        for (int i = 0; i < n - 1; i++)
        {
            for (int j = i + 1; j < n; j++)
                slopes[k++] = (samples[j] - samples[i]) / (j - i);
        }
        Array.Sort(slopes);
        int m = slopes.Length;
        return m % 2 == 1 ? slopes[m / 2] : (slopes[m / 2 - 1] + slopes[m / 2]) / 2;
    }
}
