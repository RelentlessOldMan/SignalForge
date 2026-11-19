namespace SignalForge;

/// <summary>Rosenstein's mean log divergence at each step and the exponent it gives, per sample
/// (conventions: Largest Lyapunov exponent; ADR 0354).</summary>
/// <param name="Divergence">The mean of <c>ln d_j(k)</c> over the pairs, for <c>k = 0 … steps</c>.</param>
/// <param name="Exponent">The least-squares slope of the divergence against <c>k</c>.</param>
public sealed record LargestLyapunov(double[] Divergence, double Exponent);

public static partial class Measurements
{
    /// <summary>Rosenstein's largest Lyapunov exponent: each embedded point's nearest neighbour
    /// outside the Theiler window, the mean log of their distance as both move on, and its
    /// least-squares slope (conventions: Largest Lyapunov exponent; ADR 0354).</summary>
    /// <param name="samples">Real samples, finite.</param>
    /// <param name="m">The embedding dimension, at least 1.</param>
    /// <param name="steps">How many steps to follow each pair, at least 1.</param>
    /// <param name="delay">The embedding delay in samples, at least 1.</param>
    /// <param name="theiler">The Theiler window: neighbours need <c>|j − j'|</c> above it. At least 0.</param>
    /// <returns>The divergence at each step and the exponent per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, there are too few
    /// points, or every pair has distance 0 at some step.</exception>
    public static LargestLyapunov LargestLyapunov(ReadOnlySpan<double> samples, int m, int steps, int delay = 1, int theiler = 0)
    {
        if (m < 1)
            throw new ArgumentOutOfRangeException(nameof(m), m, "must be at least 1");
        if (steps < 1)
            throw new ArgumentOutOfRangeException(nameof(steps), steps, "must be at least 1");
        if (delay < 1)
            throw new ArgumentOutOfRangeException(nameof(delay), delay, "must be at least 1");
        if (theiler < 0)
            throw new ArgumentOutOfRangeException(nameof(theiler), theiler, "must be at least 0");
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        long windows = samples.Length - ((long)(m - 1) * delay);
        long count = windows - steps;
        if (count < (2L * theiler) + 2)
            throw new ArgumentException("too few points: need Length - (m - 1)*delay - steps >= 2*theiler + 2", nameof(samples));
        int p = (int)count;
        var near = new int[p];
        for (int j = 0; j < p; j++)
        {
            double best = double.PositiveInfinity;
            for (int i = 0; i < p; i++)
            {
                if (Math.Abs(i - j) <= theiler)
                    continue;
                double d = Distance(samples, i, j, m, delay);
                if (d < best)
                {
                    best = d;
                    near[j] = i;
                }
            }
        }
        var divergence = new double[steps + 1];
        for (int s = 0; s <= steps; s++)
        {
            double sum = 0;
            int used = 0;
            for (int j = 0; j < p; j++)
            {
                double d = Distance(samples, j + s, near[j] + s, m, delay);
                if (d > 0)
                {
                    sum += Math.Log(d);
                    used++;
                }
            }
            if (used == 0)
                throw new ArgumentException("every pair has distance 0 at some step", nameof(samples));
            divergence[s] = sum / used;
        }
        double mx = steps / 2.0, my = 0;
        foreach (double v in divergence)
            my += v;
        my /= steps + 1;
        double sxy = 0, sxx = 0;
        for (int s = 0; s <= steps; s++)
        {
            sxy += (s - mx) * (divergence[s] - my);
            sxx += (s - mx) * (s - mx);
        }
        return new LargestLyapunov(divergence, sxy / sxx);

        static double Distance(ReadOnlySpan<double> x, int a, int b, int m, int delay)
        {
            double d = 0;
            for (int l = 0; l < m; l++)
                d = Math.Max(d, Math.Abs(x[a + (l * delay)] - x[b + (l * delay)]));
            return d;
        }
    }
}
