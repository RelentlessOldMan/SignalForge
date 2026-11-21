namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Smith-Wilson evenness of a record of values above 0: one less 2/pi times
    /// the arctangent of the variance of the logarithms, from 0 to 1 (conventions: the
    /// Smith-Wilson evenness; ADR 0534).</summary>
    /// <param name="samples">Real values, finite, above 0; at least 1.</param>
    /// <returns>The Smith-Wilson evenness, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double SmithWilsonEvenness(ReadOnlySpan<double> samples)
    {
        int n = samples.Length;
        if (n < 1)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        double mean = 0;
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            if (!(v > 0))
                throw new ArgumentException("samples must be above 0", nameof(samples));
            mean += Math.Log(v);
        }
        mean /= n;
        double acc = 0;
        foreach (double v in samples)
        {
            double d = Math.Log(v) - mean;
            acc += d * d;
        }
        return 1.0 - (2.0 / Math.PI * Math.Atan(acc / n));
    }
}
