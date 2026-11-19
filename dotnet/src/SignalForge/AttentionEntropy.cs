namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The mean Shannon entropy, in nats, of the four kinds of interval between strict
    /// local maxima and minima (conventions: Attention entropy; ADR 0346).</summary>
    /// <param name="samples">Real samples, finite.</param>
    /// <returns>The attention entropy in nats.</returns>
    /// <exception cref="ArgumentException">A sample is not finite, or one of the four interval
    /// sets is empty.</exception>
    public static double AttentionEntropy(ReadOnlySpan<double> samples)
    {
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        var peaks = new List<int>();
        var troughs = new List<int>();
        for (int i = 1; i < samples.Length - 1; i++)
        {
            if (samples[i] > samples[i - 1] && samples[i] > samples[i + 1])
                peaks.Add(i);
            else if (samples[i] < samples[i - 1] && samples[i] < samples[i + 1])
                troughs.Add(i);
        }
        List<int>[] sets = [Gaps(peaks), Gaps(troughs), Following(peaks, troughs), Following(troughs, peaks)];
        double total = 0;
        foreach (List<int> gaps in sets)
        {
            if (gaps.Count == 0)
                throw new ArgumentException("one of the four interval sets is empty", nameof(samples));
            var counts = new Dictionary<int, int>();
            foreach (int g in gaps)
                counts[g] = counts.GetValueOrDefault(g) + 1;
            foreach (int c in counts.Values)
            {
                double p = (double)c / gaps.Count;
                total -= p * Math.Log(p);
            }
        }
        return total / 4;

        static List<int> Gaps(List<int> at)
        {
            var g = new List<int>();
            for (int i = 1; i < at.Count; i++)
                g.Add(at[i] - at[i - 1]);
            return g;
        }

        static List<int> Following(List<int> from, List<int> to)
        {
            var g = new List<int>();
            int j = 0;
            foreach (int a in from)
            {
                while (j < to.Count && to[j] <= a)
                    j++;
                if (j < to.Count)
                    g.Add(to[j] - a);
            }
            return g;
        }
    }
}
