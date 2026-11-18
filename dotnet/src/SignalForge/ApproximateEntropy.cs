namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Pincus's approximate entropy <c>Φ_m − Φ_{m+1}</c>, self-matches counted,
    /// Chebyshev distance (conventions: Approximate entropy; ADR 0333).</summary>
    /// <param name="samples">Real samples, finite, at least <c>m + 2</c>.</param>
    /// <param name="m">The template length, at least 1.</param>
    /// <param name="r">The match tolerance in sample units, finite and at least 0.</param>
    /// <returns>The approximate entropy.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double ApproximateEntropy(ReadOnlySpan<double> samples, int m, double r)
    {
        if (m < 1)
            throw new ArgumentOutOfRangeException(nameof(m), m, "must be at least 1");
        if (!(double.IsFinite(r) && r >= 0))
            throw new ArgumentOutOfRangeException(nameof(r), r, "must be finite and at least 0");
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        if (samples.Length < m + 2)
            throw new ArgumentException("samples must be at least m + 2 long", nameof(samples));
        return ApproximateEntropyPhi(samples, m, r) - ApproximateEntropyPhi(samples, m + 1, r);
    }

    private static double ApproximateEntropyPhi(ReadOnlySpan<double> samples, int length, double r)
    {
        int n = samples.Length - length + 1;
        double total = 0;
        for (int i = 0; i < n; i++)
        {
            int matches = 0;
            for (int j = 0; j < n; j++)
            {
                bool near = true;
                for (int l = 0; l < length && near; l++)
                    near = Math.Abs(samples[j + l] - samples[i + l]) <= r;
                if (near)
                    matches++;
            }
            total += Math.Log((double)matches / n);
        }
        return total / n;
    }
}
