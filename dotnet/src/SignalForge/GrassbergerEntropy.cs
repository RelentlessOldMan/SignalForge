namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Grassberger entropy of a record of whole numbers at least 0, not all 0, in
    /// nats: Grassberger's 2003 digamma-based estimate of the Shannon entropy
    /// (conventions: the Grassberger entropy; ADR 0559).</summary>
    /// <param name="samples">Whole numbers at least 0, not all 0, totalling at most
    /// 10 000 000.</param>
    /// <returns>The Grassberger entropy in nats.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double GrassbergerEntropy(ReadOnlySpan<double> samples)
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
        double acc = 0;
        foreach (double v in samples)
        {
            if (v > 0)
            {
                double odd = 0;
                int half = (int)v / 2;
                for (int j = 0; j < half; j++)
                    odd += 2.0 / ((2 * j) + 1);
                acc += v * odd;
            }
        }
        return Math.Log(total) + 0.5772156649015329 + Math.Log(2.0) - (acc / total);
    }
}
