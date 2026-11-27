namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Lorenz curve of a record of values at least 0, not all 0: the n + 1
    /// shares of the total held by the smallest k values, from 0 to exactly 1 (conventions:
    /// the Lorenz curve; ADR 0517).</summary>
    /// <param name="samples">Real values, finite, at least 0, not all 0; at least 1.</param>
    /// <returns>The n + 1 shares, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] LorenzCurve(ReadOnlySpan<double> samples)
    {
        int n = samples.Length;
        if (n < 1)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        samples = ScaledToLargest(samples);
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            if (v < 0)
                throw new ArgumentException("samples must be at least 0", nameof(samples));
        }
        double[] sorted = samples.ToArray();
        Array.Sort(sorted);
        var sums = new double[n];
        double run = 0;
        for (int k = 0; k < n; k++)
        {
            run += sorted[k];
            sums[k] = run;
        }
        if (!(run > 0))
            throw new ArgumentException("samples must not all be 0", nameof(samples));
        var shares = new double[n + 1];
        for (int k = 0; k < n; k++)
            shares[k + 1] = sums[k] / run;
        return shares;
    }
}
