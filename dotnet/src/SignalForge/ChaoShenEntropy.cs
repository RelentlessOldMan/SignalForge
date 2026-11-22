namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Chao-Shen entropy of a record of whole numbers at least 0, not all 0, in
    /// nats: the coverage-adjusted Horvitz-Thompson estimate of the Shannon entropy
    /// (conventions: the Chao-Shen entropy; ADR 0554).</summary>
    /// <param name="samples">Whole numbers at least 0, not all 0, totalling at most
    /// 10 000 000.</param>
    /// <returns>The Chao-Shen entropy in nats, at least 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double ChaoShenEntropy(ReadOnlySpan<double> samples)
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
        int ones = 0;
        foreach (double v in samples)
        {
            if (v == 1)
                ones++;
        }
        if (ones == total)
            ones--;
        double cover = 1.0 - (ones / total);
        double acc = 0;
        foreach (double v in samples)
        {
            if (v > 0)
            {
                double share = cover * (v / total);
                acc -= share * Math.Log(share) / (1.0 - Math.Pow(1.0 - share, total));
            }
        }
        return acc;
    }
}
