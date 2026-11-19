namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Cuesta-Frau's slope entropy: each step of a window as one of five symbols by the
    /// thresholds <paramref name="gamma"/> and <paramref name="delta"/>, then the Shannon
    /// entropy in nats of the patterns (conventions: Slope entropy; ADR 0347).</summary>
    /// <param name="samples">Real samples, finite, at least <paramref name="m"/>.</param>
    /// <param name="m">The window length, from 2 to 16.</param>
    /// <param name="gamma">The steep threshold, finite and above <paramref name="delta"/>.</param>
    /// <param name="delta">The flat threshold, finite and at least 0.</param>
    /// <returns>The slope entropy in nats.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double SlopeEntropy(ReadOnlySpan<double> samples, int m, double gamma = 1, double delta = 1e-3)
    {
        if (m < 2 || m > 16)
            throw new ArgumentOutOfRangeException(nameof(m), m, "must be from 2 to 16");
        if (!(double.IsFinite(gamma) && double.IsFinite(delta) && delta >= 0 && delta < gamma))
            throw new ArgumentException("need 0 <= delta < gamma, both finite", nameof(delta));
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        int windows = samples.Length - m + 1;
        if (windows < 1)
            throw new ArgumentException("samples must be at least m long", nameof(samples));
        var symbols = new int[samples.Length - 1];
        for (int i = 0; i < symbols.Length; i++)
        {
            double d = samples[i + 1] - samples[i];
            symbols[i] = d > gamma ? 2 : d > delta ? 1 : d < -gamma ? -2 : d < -delta ? -1 : 0;
        }
        var counts = new Dictionary<long, int>();
        for (int i = 0; i < windows; i++)
        {
            long key = 0;
            for (int l = 0; l < m - 1; l++)
                key = (key * 5) + symbols[i + l] + 2;
            counts[key] = counts.GetValueOrDefault(key) + 1;
        }
        double h = 0;
        foreach (int c in counts.Values)
        {
            double p = (double)c / windows;
            h -= p * Math.Log(p);
        }
        return h;
    }
}
