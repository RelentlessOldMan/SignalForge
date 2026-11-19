namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The discrete Fisher information of the normalized singular spectrum of the
    /// delay-embedding matrix (conventions: Fisher information; ADR 0351).</summary>
    /// <param name="samples">Real samples, finite and not all 0.</param>
    /// <param name="order">The embedding dimension, from 2 to 32.</param>
    /// <param name="delay">The spacing of a row's samples, at least 1.</param>
    /// <returns>The Fisher information.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double FisherInformation(ReadOnlySpan<double> samples, int order, int delay = 1)
    {
        if (order < 2 || order > 32)
            throw new ArgumentOutOfRangeException(nameof(order), order, "must be from 2 to 32");
        if (delay < 1)
            throw new ArgumentOutOfRangeException(nameof(delay), delay, "must be at least 1");
        bool any = false;
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            any |= v != 0;
        }
        long rows = samples.Length - (long)(order - 1) * delay;
        if (rows < order)
            throw new ArgumentException("samples are too short: need Length - (order - 1)*delay >= order", nameof(samples));
        if (!any)
            throw new ArgumentException("samples must not all be 0", nameof(samples));
        int k = (int)rows;
        var columns = new double[order][];
        for (int j = 0; j < order; j++)
            columns[j] = samples.Slice(j * delay, k).ToArray();
        double[] s = SingularValuesByJacobi(columns);
        Array.Sort(s);
        Array.Reverse(s);
        double total = 0;
        foreach (double v in s)
            total += v;
        double f = 0;
        for (int i = 0; i < order - 1; i++)
        {
            double p = s[i] / total;
            if (p > 0)
            {
                double step = (s[i + 1] / total) - p;
                f += step * step / p;
            }
        }
        return f;
    }
}
