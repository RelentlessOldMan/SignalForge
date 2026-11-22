namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Patil-Taillie diversity of order <paramref name="beta"/> of a record of
    /// values at least 0, not all 0: (1 - sum p^(beta+1))/beta over the shares above 0, the
    /// Shannon entropy at beta = 0 (conventions: the Patil-Taillie diversity;
    /// ADR 0565).</summary>
    /// <param name="samples">Real values, finite, at least 0, not all 0; at least 1.</param>
    /// <param name="beta">The order, finite and at least -1.</param>
    /// <returns>The Patil-Taillie diversity.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double PatilTaillieDiversity(ReadOnlySpan<double> samples, double beta)
    {
        if (!double.IsFinite(beta) || !(beta >= -1))
            throw new ArgumentException("beta must be finite and at least -1", nameof(beta));
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
        if (beta == 0)
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
        foreach (double v in samples)
        {
            if (v > 0)
            {
                double p = v / total;
                acc += p * Spectral.ExpM1(beta * Math.Log(p));
            }
        }
        return -acc / beta;
    }
}
