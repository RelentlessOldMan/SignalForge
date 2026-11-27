namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The binary Shannon entropy in bits of the share of embedded-vector pairs whose
    /// angular distance is below <paramref name="r"/> (conventions: Cosine similarity entropy;
    /// ADR 0358).</summary>
    /// <param name="samples">Real samples, finite.</param>
    /// <param name="m">The embedding dimension, at least 1.</param>
    /// <param name="r">The angular-distance threshold, above 0 and at most 1.</param>
    /// <param name="delay">The embedding delay, at least 1.</param>
    /// <returns>The cosine similarity entropy in bits.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or an embedded vector is all zeros.</exception>
    public static double CosineSimilarityEntropy(ReadOnlySpan<double> samples, int m, double r, int delay = 1)
    {
        if (m < 1)
            throw new ArgumentOutOfRangeException(nameof(m), m, "must be at least 1");
        if (delay < 1)
            throw new ArgumentOutOfRangeException(nameof(delay), delay, "must be at least 1");
        if (!(r > 0 && r <= 1))
            throw new ArgumentOutOfRangeException(nameof(r), r, "must be above 0 and at most 1");
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        samples = ScaledByPowerOf2(samples);
        long w = samples.Length - (long)(m - 1) * delay;
        if (w < 2)
            throw new ArgumentException("there must be at least two embedded vectors", nameof(samples));
        var norms = new double[w];
        for (int i = 0; i < w; i++)
        {
            double s = 0;
            for (int k = 0; k < m; k++)
                s += samples[i + k * delay] * samples[i + k * delay];
            norms[i] = Math.Sqrt(s);
            if (!(norms[i] > 0))
                throw new ArgumentException("no embedded vector may be all zeros", nameof(samples));
        }
        long similar = 0;
        for (int i = 0; i < w; i++)
        {
            for (int j = i + 1; j < w; j++)
            {
                double dot = 0;
                for (int k = 0; k < m; k++)
                    dot += samples[i + k * delay] * samples[j + k * delay];
                double c = Math.Clamp(dot / (norms[i] * norms[j]), -1.0, 1.0);
                if (Math.Acos(c) / Math.PI < r)
                    similar++;
            }
        }
        double b = similar / (w * (w - 1) / 2.0);
        if (b == 0 || b == 1)
            return 0;
        return -b * Math.Log2(b) - (1 - b) * Math.Log2(1 - b);
    }
}
