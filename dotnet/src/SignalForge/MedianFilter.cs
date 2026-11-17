namespace SignalForge;

public static partial class Dsp
{
    /// <summary>Running median over a symmetric window of <paramref name="length"/> samples that
    /// shrinks at the ends to stay inside the data (conventions: Running median filter; ADR
    /// 0234).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="length">The window length, odd and at least 1.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] MedianFilter(ReadOnlySpan<double> samples, int length)
    {
        if (length < 1 || length % 2 == 0)
            throw new ArgumentOutOfRangeException(nameof(length), "length must be odd and at least 1");
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        int h = (length - 1) / 2;
        int n = samples.Length;
        var y = new double[n];
        var buf = new double[length];
        for (int i = 0; i < n; i++)
        {
            int w = Math.Min(h, Math.Min(i, n - 1 - i));
            Span<double> win = buf.AsSpan(0, 2 * w + 1);
            samples.Slice(i - w, 2 * w + 1).CopyTo(win);
            win.Sort();
            y[i] = win[w];
        }
        return y;
    }

    private const double MadScale = 1.482602218505602;

    /// <summary>Replaces each sample further than <paramref name="threshold"/> robust standard
    /// deviations (1.4826 MAD) from its window median by that median (conventions: Hampel filter;
    /// ADR 0235).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="length">The window length, odd and at least 1.</param>
    /// <param name="threshold">The threshold in robust standard deviations, finite and at least
    /// 0.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] HampelFilter(ReadOnlySpan<double> samples, int length, double threshold = 3.0)
    {
        if (length < 1 || length % 2 == 0)
            throw new ArgumentOutOfRangeException(nameof(length), "length must be odd and at least 1");
        if (!double.IsFinite(threshold) || threshold < 0)
            throw new ArgumentOutOfRangeException(nameof(threshold), "threshold must be finite and non-negative");
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        int h = (length - 1) / 2;
        int n = samples.Length;
        var y = samples.ToArray();
        var buf = new double[length];
        double k = threshold * MadScale;
        for (int i = 0; i < n; i++)
        {
            int w = Math.Min(h, Math.Min(i, n - 1 - i));
            Span<double> win = buf.AsSpan(0, 2 * w + 1);
            samples.Slice(i - w, 2 * w + 1).CopyTo(win);
            win.Sort();
            double med = win[w];
            for (int j = 0; j < win.Length; j++)
                win[j] = Math.Abs(samples[i - w + j] - med);
            win.Sort();
            double mad = win[w];
            if (Math.Abs(samples[i] - med) > k * mad)
                y[i] = med;
        }
        return y;
    }
}
