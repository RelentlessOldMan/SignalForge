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
}
