namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Li et al.'s distribution entropy: the Shannon entropy of the histogram of
    /// Chebyshev distances between windows, over <c>ln(bins)</c> (conventions: Distribution
    /// entropy; ADR 0348).</summary>
    /// <param name="samples">Real samples, finite, at least <c>m + 1</c>.</param>
    /// <param name="m">The window length, at least 1.</param>
    /// <param name="bins">The number of histogram bins, from 2 to 1 000 000.</param>
    /// <returns>The distribution entropy, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double DistributionEntropy(ReadOnlySpan<double> samples, int m, int bins = 512)
    {
        if (m < 1)
            throw new ArgumentOutOfRangeException(nameof(m), m, "must be at least 1");
        if (bins < 2 || bins > 1_000_000)
            throw new ArgumentOutOfRangeException(nameof(bins), bins, "must be from 2 to 1000000");
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        int windows = samples.Length - m + 1;
        if (windows < 2)
            throw new ArgumentException("samples must be at least m + 1 long", nameof(samples));
        var d = new double[(long)windows * (windows - 1) / 2];
        int n = 0;
        for (int i = 0; i < windows - 1; i++)
        {
            for (int j = i + 1; j < windows; j++)
            {
                double dist = 0;
                for (int l = 0; l < m; l++)
                    dist = Math.Max(dist, Math.Abs(samples[j + l] - samples[i + l]));
                d[n++] = dist;
            }
        }
        double lo = double.PositiveInfinity, hi = double.NegativeInfinity;
        foreach (double v in d)
        {
            lo = Math.Min(lo, v);
            hi = Math.Max(hi, v);
        }
        if (!(hi > lo))
            return 0;
        var counts = new long[bins];
        foreach (double v in d)
            counts[(int)Math.Min(bins - 1, Math.Floor((v - lo) * bins / (hi - lo)))]++;
        double h = 0;
        foreach (long c in counts)
        {
            if (c == 0)
                continue;
            double p = (double)c / d.Length;
            h -= p * Math.Log(p);
        }
        return h / Math.Log(bins);
    }
}
