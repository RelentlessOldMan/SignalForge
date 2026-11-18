namespace SignalForge;

public static partial class Measurements
{
    /// <summary><c>−ln(A/B)</c>, <c>B</c> and <c>A</c> the pairs of templates that stay within
    /// <paramref name="r"/> (Chebyshev) for <paramref name="m"/> and <c>m + 1</c> samples
    /// (conventions: Sample entropy; ADR 0326).</summary>
    /// <param name="samples">Real samples, finite, at least <c>m + 2</c>.</param>
    /// <param name="m">The template length, at least 1.</param>
    /// <param name="r">The match tolerance in sample units, finite and at least 0.</param>
    /// <returns>The sample entropy; +∞ when no template pair matches for <c>m + 1</c>.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or no pair matches
    /// for <paramref name="m"/>.</exception>
    public static double SampleEntropy(ReadOnlySpan<double> samples, int m, double r)
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
        int starts = samples.Length - m;
        if (starts < 2)
            throw new ArgumentException("samples must be at least m + 2 long", nameof(samples));
        long b = 0, a = 0;
        for (int i = 0; i < starts - 1; i++)
        {
            for (int l = i + 1; l < starts; l++)
            {
                bool near = true;
                for (int j = 0; j < m && near; j++)
                    near = Math.Abs(samples[l + j] - samples[i + j]) <= r;
                if (!near)
                    continue;
                b++;
                if (Math.Abs(samples[l + m] - samples[i + m]) <= r)
                    a++;
            }
        }
        if (b == 0)
            throw new ArgumentException("no two templates match, so sample entropy is undefined", nameof(samples));
        return a == 0 ? double.PositiveInfinity : -Math.Log((double)a / b);
    }
}
