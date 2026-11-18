namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Higuchi's fractal dimension: the least-squares slope of <c>ln L(k)</c> against
    /// <c>ln(1/k)</c> for <c>k = 1 … kMax</c> (conventions: Higuchi fractal dimension;
    /// ADR 0330).</summary>
    /// <param name="samples">Real samples, finite, at least <c>2·kMax</c>, not constant.</param>
    /// <param name="kMax">The largest step, at least 2.</param>
    /// <returns>The dimension, near 1 for a smooth curve and 2 for white noise.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double HiguchiDimension(ReadOnlySpan<double> samples, int kMax)
    {
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        int size = samples.Length;
        if (kMax < 2 || kMax > size / 2)
            throw new ArgumentOutOfRangeException(nameof(kMax), kMax, "must be at least 2 with 2·kMax <= samples.Length");
        var lx = new double[kMax];
        var ly = new double[kMax];
        for (int k = 1; k <= kMax; k++)
        {
            double total = 0;
            for (int m = 0; m < k; m++)
            {
                int steps = (size - 1 - m) / k;
                double sum = 0;
                for (int i = 1; i <= steps; i++)
                    sum += Math.Abs(samples[m + (i * k)] - samples[m + ((i - 1) * k)]);
                total += sum * (size - 1) / ((double)steps * k) / k;
            }
            double length = total / k;
            if (!(length > 0))
                throw new ArgumentException("the curve must have a length at every k", nameof(samples));
            lx[k - 1] = -Math.Log(k);
            ly[k - 1] = Math.Log(length);
        }
        double mx = 0, my = 0;
        for (int k = 0; k < kMax; k++)
        {
            mx += lx[k];
            my += ly[k];
        }
        mx /= kMax;
        my /= kMax;
        double sxy = 0, sxx = 0;
        for (int k = 0; k < kMax; k++)
        {
            sxy += (lx[k] - mx) * (ly[k] - my);
            sxx += (lx[k] - mx) * (lx[k] - mx);
        }
        return sxy / sxx;
    }
}
