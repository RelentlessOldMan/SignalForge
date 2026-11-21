namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The generalized entropy index of order <paramref name="alpha"/> of a record
    /// of positive values: the mean log deviation at 0, the Theil index at 1, at least 0
    /// (conventions: the generalized entropy index; ADR 0516).</summary>
    /// <param name="samples">Real values, finite, greater than 0; at least 1.</param>
    /// <param name="alpha">The order, finite.</param>
    /// <returns>The generalized entropy index, at least 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double GeneralizedEntropyIndex(ReadOnlySpan<double> samples, double alpha)
    {
        if (!double.IsFinite(alpha))
            throw new ArgumentException("alpha must be finite", nameof(alpha));
        int n = samples.Length;
        if (n < 1)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        double total = 0;
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            if (!(v > 0))
                throw new ArgumentException("samples must be greater than 0", nameof(samples));
            total += v;
        }
        double mean = total / n;
        double sum = 0;
        foreach (double v in samples)
        {
            double ratio = v / mean;
            if (alpha == 0)
                sum -= Math.Log(ratio);
            else if (alpha == 1)
                sum += ratio * Math.Log(ratio);
            else
                sum += Math.Pow(ratio, alpha) - 1.0;
        }
        return alpha == 0 || alpha == 1 ? sum / n : sum / n / (alpha * (alpha - 1.0));
    }
}
