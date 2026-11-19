namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Fraser and Swinney's auto mutual information: the mutual information in nats
    /// between <c>x_t</c> and <c>x_{t+lag}</c> from an equal-width histogram, at each lag
    /// (conventions: Auto mutual information; ADR 0352).</summary>
    /// <param name="samples">Real samples, finite and not all equal.</param>
    /// <param name="lags">At least one lag, each from 0 to <c>samples.Length − 1</c>.</param>
    /// <param name="bins">The number of bins per coordinate, from 2 to 4096.</param>
    /// <returns>The mutual information at each lag, in the order given.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] AutoMutualInformation(ReadOnlySpan<double> samples, ReadOnlySpan<int> lags, int bins = 16)
    {
        if (bins < 2 || bins > 4096)
            throw new ArgumentOutOfRangeException(nameof(bins), bins, "must be from 2 to 4096");
        double lo = double.PositiveInfinity, hi = double.NegativeInfinity;
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            lo = Math.Min(lo, v);
            hi = Math.Max(hi, v);
        }
        if (lags.Length < 1)
            throw new ArgumentException("lags must have at least one entry", nameof(lags));
        foreach (int t in lags)
        {
            if (t < 0 || t > samples.Length - 1)
                throw new ArgumentException("each lag must be from 0 to samples.Length - 1", nameof(lags));
        }
        if (!(hi > lo))
            throw new ArgumentException("samples must not all be equal", nameof(samples));
        var b = new int[samples.Length];
        for (int i = 0; i < b.Length; i++)
            b[i] = (int)Math.Min(bins - 1, Math.Floor((samples[i] - lo) * bins / (hi - lo)));
        var result = new double[lags.Length];
        var ca = new long[bins];
        var cb = new long[bins];
        var joint = new long[bins * bins];
        for (int f = 0; f < lags.Length; f++)
        {
            int t = lags[f];
            int n = samples.Length - t;
            Array.Clear(ca);
            Array.Clear(cb);
            Array.Clear(joint);
            for (int i = 0; i < n; i++)
            {
                ca[b[i]]++;
                cb[b[i + t]]++;
                joint[(b[i] * bins) + b[i + t]]++;
            }
            double mi = 0;
            for (int k = 0; k < joint.Length; k++)
            {
                if (joint[k] == 0)
                    continue;
                double c = joint[k];
                mi += c / n * Math.Log(c * n / ((double)ca[k / bins] * cb[k % bins]));
            }
            result[f] = mi;
        }
        return result;
    }
}
