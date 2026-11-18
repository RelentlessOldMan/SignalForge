namespace SignalForge;

/// <summary>Mean rescaled ranges and the Hurst exponent they give (conventions: Rescaled range;
/// ADR 0340).</summary>
/// <param name="Scales">The box sizes in samples, in the order given.</param>
/// <param name="Values">The mean <c>R/S</c> over the boxes at each size.</param>
/// <param name="Hurst">The least-squares slope of <c>ln(R/S)</c> against <c>ln s</c>.</param>
public sealed record RescaledRange(int[] Scales, double[] Values, double Hurst);

public static partial class Measurements
{
    /// <summary>Hurst's rescaled-range analysis: the mean <c>R/S</c> over non-overlapping boxes
    /// of each size, and the least-squares slope of its logarithm against <c>ln s</c>
    /// (conventions: Rescaled range; ADR 0340).</summary>
    /// <param name="samples">Real samples, finite.</param>
    /// <param name="scales">At least two box sizes, strictly increasing, each from 4 to the
    /// number of samples.</param>
    /// <returns>The scales, the mean rescaled range at each, and the Hurst exponent.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or a box is constant.</exception>
    public static RescaledRange RescaledRange(ReadOnlySpan<double> samples, ReadOnlySpan<int> scales)
    {
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        int size = samples.Length;
        if (scales.Length < 2)
            throw new ArgumentException("scales must have at least two entries", nameof(scales));
        for (int i = 0; i < scales.Length; i++)
        {
            if (scales[i] < 4 || scales[i] > size)
                throw new ArgumentException("each scale must be at least 4 and at most samples.Length", nameof(scales));
            if (i > 0 && scales[i] <= scales[i - 1])
                throw new ArgumentException("scales must be strictly increasing", nameof(scales));
        }
        var values = new double[scales.Length];
        for (int f = 0; f < scales.Length; f++)
        {
            int s = scales[f];
            int boxes = size / s;
            double total = 0;
            for (int b = 0; b < boxes; b++)
            {
                ReadOnlySpan<double> box = samples.Slice(b * s, s);
                double mean = 0;
                foreach (double v in box)
                    mean += v;
                mean /= s;
                double z = 0, hi = double.NegativeInfinity, lo = double.PositiveInfinity, squares = 0;
                foreach (double v in box)
                {
                    double y = v - mean;
                    z += y;
                    hi = Math.Max(hi, z);
                    lo = Math.Min(lo, z);
                    squares += y * y;
                }
                double spread = Math.Sqrt(squares / s);
                if (!(spread > 0))
                    throw new ArgumentException("every box must vary", nameof(samples));
                total += (hi - lo) / spread;
            }
            values[f] = total / boxes;
        }
        double mx = 0, my = 0;
        for (int f = 0; f < scales.Length; f++)
        {
            mx += Math.Log(scales[f]);
            my += Math.Log(values[f]);
        }
        mx /= scales.Length;
        my /= scales.Length;
        double sxy = 0, sxx = 0;
        for (int f = 0; f < scales.Length; f++)
        {
            double dx = Math.Log(scales[f]) - mx;
            sxy += dx * (Math.Log(values[f]) - my);
            sxx += dx * dx;
        }
        return new RescaledRange(scales.ToArray(), values, sxy / sxx);
    }
}
