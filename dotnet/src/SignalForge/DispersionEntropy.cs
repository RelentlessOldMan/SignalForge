namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Rostaghi and Azami's dispersion entropy: normal-CDF classes, then the Shannon
    /// entropy of the class patterns over <c>ln(classesᵐ)</c> (conventions: Dispersion entropy;
    /// ADR 0341).</summary>
    /// <param name="samples">Real samples, finite and not constant.</param>
    /// <param name="m">The pattern length, from 1 to 10.</param>
    /// <param name="classes">The number of classes, from 2 to 64.</param>
    /// <param name="delay">The spacing of a pattern's samples, at least 1.</param>
    /// <returns>The dispersion entropy, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double DispersionEntropy(ReadOnlySpan<double> samples, int m, int classes, int delay = 1)
    {
        if (m < 1 || m > 10)
            throw new ArgumentOutOfRangeException(nameof(m), m, "must be from 1 to 10");
        if (classes < 2 || classes > 64)
            throw new ArgumentOutOfRangeException(nameof(classes), classes, "must be from 2 to 64");
        if (delay < 1)
            throw new ArgumentOutOfRangeException(nameof(delay), delay, "must be at least 1");
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        long windows = samples.Length - (long)(m - 1) * delay;
        if (windows < 1)
            throw new ArgumentException("samples are too short for one pattern", nameof(samples));
        double mu = 0;
        foreach (double v in samples)
            mu += v;
        mu /= samples.Length;
        double squares = 0;
        foreach (double v in samples)
            squares += (v - mu) * (v - mu);
        double sigma = Math.Sqrt(squares / samples.Length);
        if (!(sigma > 0))
            throw new ArgumentException("samples must not be constant", nameof(samples));
        double scale = sigma * Math.Sqrt(2);
        var z = new int[samples.Length];
        for (int i = 0; i < samples.Length; i++)
        {
            double y = 0.5 * SpecialFunctions.Erfc(-(samples[i] - mu) / scale);
            z[i] = Math.Min(classes, (int)Math.Floor(classes * y) + 1);
        }
        var counts = new Dictionary<long, int>();
        for (int i = 0; i < windows; i++)
        {
            long key = 0;
            for (int l = 0; l < m; l++)
                key = key * classes + (z[i + l * delay] - 1);
            counts[key] = counts.GetValueOrDefault(key) + 1;
        }
        double h = 0;
        foreach (int n in counts.Values)
        {
            double p = (double)n / windows;
            h -= p * Math.Log(p);
        }
        return h / (m * Math.Log(classes));
    }
}
