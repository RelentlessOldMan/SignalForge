namespace SignalForge;

/// <summary>The correlation sum at each radius and the correlation dimension it gives
/// (conventions: Correlation sum; ADR 0349).</summary>
/// <param name="Radii">The radii, in the order given.</param>
/// <param name="Values">The share of pairs closer than each radius.</param>
/// <param name="Dimension">The least-squares slope of <c>ln C</c> against <c>ln r</c>.</param>
public sealed record CorrelationSum(double[] Radii, double[] Values, double Dimension);

public static partial class Measurements
{
    /// <summary>Grassberger and Procaccia's correlation sum: the share of embedded pairs closer
    /// than each radius in the Chebyshev distance, and the least-squares slope of its logarithm
    /// against <c>ln r</c> (conventions: Correlation sum; ADR 0349).</summary>
    /// <param name="samples">Real samples, finite.</param>
    /// <param name="m">The embedding dimension, at least 1.</param>
    /// <param name="radii">At least two radii, finite, positive and strictly increasing.</param>
    /// <param name="delay">The embedding delay in samples, at least 1.</param>
    /// <param name="theiler">The Theiler window: pairs need <c>j − i</c> above it. At least 0.</param>
    /// <returns>The radii, the correlation sum at each, and the correlation dimension.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, there is no pair, or a
    /// radius has no pair closer than it.</exception>
    public static CorrelationSum CorrelationSum(ReadOnlySpan<double> samples, int m, ReadOnlySpan<double> radii, int delay = 1, int theiler = 0)
    {
        if (m < 1)
            throw new ArgumentOutOfRangeException(nameof(m), m, "must be at least 1");
        if (delay < 1)
            throw new ArgumentOutOfRangeException(nameof(delay), delay, "must be at least 1");
        if (theiler < 0)
            throw new ArgumentOutOfRangeException(nameof(theiler), theiler, "must be at least 0");
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        if (radii.Length < 2)
            throw new ArgumentException("radii must have at least two entries", nameof(radii));
        for (int i = 0; i < radii.Length; i++)
        {
            if (!double.IsFinite(radii[i]) || !(radii[i] > 0) || (i > 0 && !(radii[i] > radii[i - 1])))
                throw new ArgumentException("radii must be finite, positive and strictly increasing", nameof(radii));
        }
        long windows = samples.Length - ((long)(m - 1) * delay);
        if (windows - theiler < 2)
            throw new ArgumentException("there must be at least one pair", nameof(samples));
        int w = (int)windows;
        var d = new List<double>();
        for (int s = theiler + 1; s < w; s++)
        {
            for (int i = 0; i + s < w; i++)
            {
                double dist = 0;
                for (int l = 0; l < m; l++)
                    dist = Math.Max(dist, Math.Abs(samples[i + s + (l * delay)] - samples[i + (l * delay)]));
                d.Add(dist);
            }
        }
        d.Sort();
        var values = new double[radii.Length];
        for (int f = 0; f < radii.Length; f++)
        {
            int lo = 0, hi = d.Count;
            while (lo < hi)
            {
                int mid = (lo + hi) >>> 1;
                if (d[mid] < radii[f])
                    lo = mid + 1;
                else
                    hi = mid;
            }
            if (lo == 0)
                throw new ArgumentException("every radius must have a pair closer than it", nameof(radii));
            values[f] = (double)lo / d.Count;
        }
        double mx = 0, my = 0;
        for (int f = 0; f < radii.Length; f++)
        {
            mx += Math.Log(radii[f]);
            my += Math.Log(values[f]);
        }
        mx /= radii.Length;
        my /= radii.Length;
        double sxy = 0, sxx = 0;
        for (int f = 0; f < radii.Length; f++)
        {
            double dx = Math.Log(radii[f]) - mx;
            sxy += dx * (Math.Log(values[f]) - my);
            sxx += dx * dx;
        }
        return new CorrelationSum(radii.ToArray(), values, sxy / sxx);
    }
}
