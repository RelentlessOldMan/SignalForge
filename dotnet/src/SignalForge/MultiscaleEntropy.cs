namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Costa's multiscale entropy: the sample entropy of the non-overlapping
    /// coarse-grained means at each scale, <paramref name="r"/> the same at every scale
    /// (conventions: Multiscale entropy; ADR 0338).</summary>
    /// <param name="samples">Real samples, finite.</param>
    /// <param name="m">The template length, at least 1.</param>
    /// <param name="r">The match tolerance in sample units, finite and at least 0.</param>
    /// <param name="scales">The scales, at least one, each at least 1 with
    /// <c>floor(N/τ) ≥ m + 2</c>.</param>
    /// <returns>The sample entropy at each scale, in the scales' order.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or no pair matches for
    /// <paramref name="m"/> at some scale.</exception>
    public static double[] MultiscaleEntropy(ReadOnlySpan<double> samples, int m, double r, ReadOnlySpan<int> scales)
    {
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        if (m < 1)
            throw new ArgumentOutOfRangeException(nameof(m), m, "must be at least 1");
        if (scales.IsEmpty)
            throw new ArgumentException("scales must not be empty", nameof(scales));
        foreach (int s in scales)
        {
            if (s < 1 || samples.Length / s < m + 2)
                throw new ArgumentException("each scale must be at least 1 with N / scale >= m + 2", nameof(scales));
        }
        var result = new double[scales.Length];
        for (int f = 0; f < scales.Length; f++)
        {
            int s = scales[f];
            var coarse = new double[samples.Length / s];
            for (int j = 0; j < coarse.Length; j++)
            {
                double sum = 0;
                for (int i = j * s; i < (j + 1) * s; i++)
                    sum += samples[i];
                coarse[j] = sum / s;
            }
            result[f] = SampleEntropy(coarse, m, r);
        }
        return result;
    }
}
