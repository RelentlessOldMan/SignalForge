namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Zhang's entropy of a record of whole numbers at least 0 totalling more than 1
    /// and at most 10 000, in nats: Zhang's 2012 estimate of the Shannon entropy
    /// (conventions: Zhang's entropy; ADR 0561).</summary>
    /// <param name="samples">Whole numbers at least 0, totalling more than 1 and at most
    /// 10 000.</param>
    /// <returns>Zhang's entropy in nats.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double ZhangEntropy(ReadOnlySpan<double> samples)
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
        if (total > 10_000)
            throw new ArgumentException("samples must total at most 10 000", nameof(samples));
        if (!(total > 1))
            throw new ArgumentException("samples must total more than 1", nameof(samples));
        Dictionary<double, double> inner = new();
        double acc = 0;
        foreach (double v in samples)
        {
            if (v > 0)
            {
                if (!inner.TryGetValue(v, out double part))
                {
                    double prod = 1;
                    part = 0;
                    int stop = (int)(total - v);
                    for (int step = 1; step <= stop; step++)
                    {
                        prod *= 1.0 - ((v - 1.0) / (total - step));
                        part += prod / step;
                    }
                    inner[v] = part;
                }
                acc += v / total * part;
            }
        }
        return acc;
    }
}
