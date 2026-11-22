namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Miller-Madow entropy of a record of whole numbers at least 0, not all 0,
    /// in nats: the plug-in Shannon entropy plus (k - 1)/(2N)
    /// (conventions: the Miller-Madow entropy; ADR 0555).</summary>
    /// <param name="samples">Whole numbers at least 0, not all 0, totalling at most
    /// 10 000 000.</param>
    /// <returns>The Miller-Madow entropy in nats, at least 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double MillerMadowEntropy(ReadOnlySpan<double> samples)
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
        double acc = 0;
        foreach (double v in samples)
        {
            if (v > 0)
            {
                k++;
                double share = v / total;
                acc -= share * Math.Log(share);
            }
        }
        return acc + ((k - 1) / (2.0 * total));
    }
}
