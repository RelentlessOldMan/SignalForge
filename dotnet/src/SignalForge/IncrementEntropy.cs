namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Shannon entropy in nats of words of <paramref name="m"/> increment letters,
    /// each the sign and the quantized size of a step (conventions: Increment entropy;
    /// ADR 0344).</summary>
    /// <param name="samples">Real samples, finite, at least <c>m + 1</c>, not all steps 0.</param>
    /// <param name="m">The word length in increments, at least 1.</param>
    /// <param name="levels">The number of size levels <c>R</c>, from 1 to 1000.</param>
    /// <returns>The increment entropy in nats.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double IncrementEntropy(ReadOnlySpan<double> samples, int m, int levels)
    {
        if (m < 1)
            throw new ArgumentOutOfRangeException(nameof(m), m, "must be at least 1");
        if (levels < 1 || levels > 1000)
            throw new ArgumentOutOfRangeException(nameof(levels), levels, "must be from 1 to 1000");
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        int words = samples.Length - m;
        if (words < 1)
            throw new ArgumentException("samples must be at least m + 1 long", nameof(samples));
        int n = samples.Length - 1;
        var step = new double[n];
        double mean = 0;
        for (int i = 0; i < n; i++)
        {
            step[i] = samples[i + 1] - samples[i];
            mean += step[i];
        }
        mean /= n;
        double squares = 0;
        foreach (double v in step)
            squares += (v - mean) * (v - mean);
        double sigma = Math.Sqrt(squares / n);
        if (!(sigma > 0))
            throw new ArgumentException("the increments must not all be 0", nameof(samples));
        var letters = new char[n];
        for (int i = 0; i < n; i++)
        {
            int size = (int)Math.Min(levels, Math.Floor(Math.Abs(step[i]) * levels / sigma));
            letters[i] = (char)(((Math.Sign(step[i]) + 1) * (levels + 1)) + size);
        }
        var counts = new Dictionary<string, int>(StringComparer.Ordinal);
        for (int i = 0; i < words; i++)
        {
            string key = new(letters, i, m);
            counts[key] = counts.GetValueOrDefault(key) + 1;
        }
        double h = 0;
        foreach (int c in counts.Values)
        {
            double p = (double)c / words;
            h -= p * Math.Log(p);
        }
        return h;
    }
}
