namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Manis et al.'s bubble entropy: Rényi-2 entropies of the bubble-sort swap counts
    /// of windows of <paramref name="m"/> and <c>m + 1</c> samples (conventions: Bubble entropy;
    /// ADR 0345).</summary>
    /// <param name="samples">Real samples, finite, at least <c>m + 1</c>.</param>
    /// <param name="m">The window length, from 2 to 64.</param>
    /// <returns>The bubble entropy.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double BubbleEntropy(ReadOnlySpan<double> samples, int m)
    {
        if (m < 2 || m > 64)
            throw new ArgumentOutOfRangeException(nameof(m), m, "must be from 2 to 64");
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        if (samples.Length < m + 1)
            throw new ArgumentException("samples must be at least m + 1 long", nameof(samples));
        return (BubbleRenyi(samples, m + 1) - BubbleRenyi(samples, m)) / Math.Log((m + 1.0) / (m - 1));
    }

    private static double BubbleRenyi(ReadOnlySpan<double> samples, int length)
    {
        int windows = samples.Length - length + 1;
        var counts = new long[(length * (length - 1) / 2) + 1];
        for (int i = 0; i < windows; i++)
        {
            int swaps = 0;
            for (int j = 0; j < length - 1; j++)
            {
                for (int l = j + 1; l < length; l++)
                {
                    if (samples[i + j] > samples[i + l])
                        swaps++;
                }
            }
            counts[swaps]++;
        }
        double sum = 0;
        foreach (long c in counts)
        {
            double p = (double)c / windows;
            sum += p * p;
        }
        return -Math.Log(sum);
    }
}
