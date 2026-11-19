namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The order-<paramref name="q"/> Tsallis entropy of an equal-width histogram of
    /// the samples, Shannon's in nats at <c>q = 1</c> (conventions: Tsallis entropy;
    /// ADR 0356).</summary>
    /// <param name="samples">Real samples, finite and not all equal.</param>
    /// <param name="q">The order, finite and at least 0.</param>
    /// <param name="bins">The number of bins, from 2 to 4096.</param>
    /// <returns>The Tsallis entropy.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double TsallisEntropy(ReadOnlySpan<double> samples, double q, int bins = 16)
    {
        if (!double.IsFinite(q) || !(q >= 0))
            throw new ArgumentOutOfRangeException(nameof(q), q, "must be finite and at least 0");
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
        if (!(hi > lo))
            throw new ArgumentException("samples must not all be equal", nameof(samples));
        var counts = new long[bins];
        foreach (double v in samples)
            counts[(int)Math.Min(bins - 1, Math.Floor((v - lo) * bins / (hi - lo)))]++;
        double shannon = 0, power = 0;
        foreach (long c in counts)
        {
            if (c == 0)
                continue;
            double p = (double)c / samples.Length;
            shannon -= p * Math.Log(p);
            power += Math.Pow(p, q);
        }
        return q == 1 ? shannon : (1 - power) / (q - 1);
    }
}
