namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Camargo's evenness of a record of values at least 0, not all 0: one less the
    /// sum of the gaps between every pair of shares over n, from 1/n to 1 (conventions:
    /// Camargo's evenness; ADR 0533).</summary>
    /// <param name="samples">Real values, finite, at least 0, not all 0; at least 1.</param>
    /// <returns>Camargo's evenness, from 1/n to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double CamargoEvenness(ReadOnlySpan<double> samples)
    {
        int n = samples.Length;
        if (n < 1)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        samples = ScaledToLargest(samples);
        double total = 0;
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            if (v < 0)
                throw new ArgumentException("samples must be at least 0", nameof(samples));
            total += v;
        }
        if (!(total > 0))
            throw new ArgumentException("samples must not all be 0", nameof(samples));
        double[] shares = new double[n];
        for (int i = 0; i < n; i++)
            shares[i] = samples[i] / total;
        double acc = 0;
        for (int i = 0; i < n; i++)
        {
            for (int j = i + 1; j < n; j++)
                acc += Math.Abs(shares[i] - shares[j]);
        }
        return 1.0 - (acc / n);
    }
}
