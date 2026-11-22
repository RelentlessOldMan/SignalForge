namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Tsallis diversity of order <paramref name="order"/> of a record of values
    /// at least 0, not all 0: (1 - sum p^q)/(q - 1) over the shares above 0, the Shannon
    /// entropy at q = 1 (conventions: the Tsallis diversity of counts; ADR 0568).</summary>
    /// <param name="samples">Real values, finite, at least 0, not all 0; at least 1.</param>
    /// <param name="order">The order q, finite and at least 0.</param>
    /// <returns>The Tsallis diversity.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double TsallisDiversity(ReadOnlySpan<double> samples, double order)
    {
        if (!double.IsFinite(order) || !(order >= 0))
            throw new ArgumentException("order must be finite and at least 0", nameof(order));
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
            total += v;
        }
        if (!(total > 0))
            throw new ArgumentException("samples must not all be 0", nameof(samples));
        double acc = 0;
        if (order == 1)
        {
            foreach (double v in samples)
            {
                if (v > 0)
                {
                    double p = v / total;
                    acc += p * Math.Log(p);
                }
            }
            return -acc;
        }
        double b = order - 1.0;
        foreach (double v in samples)
        {
            if (v > 0)
            {
                double p = v / total;
                acc += p * Spectral.ExpM1(b * Math.Log(p));
            }
        }
        return -acc / b;
    }
}
