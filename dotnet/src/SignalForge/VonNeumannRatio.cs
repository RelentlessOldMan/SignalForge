namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The sum of squared successive differences over the sum of squared deviations
    /// from the mean, about 2 for an i.i.d. record (conventions: von Neumann ratio;
    /// ADR 0362).</summary>
    /// <param name="samples">Real samples, finite, at least 2 and not all equal.</param>
    /// <returns>The von Neumann ratio.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double VonNeumannRatio(ReadOnlySpan<double> samples)
    {
        if (samples.Length < 2)
            throw new ArgumentException("samples must have at least 2 values", nameof(samples));
        double sum = 0;
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            sum += v;
        }
        double mean = sum / samples.Length;
        double den = 0, num = 0;
        for (int t = 0; t < samples.Length; t++)
        {
            double d = samples[t] - mean;
            den += d * d;
            if (t > 0)
            {
                double s = samples[t] - samples[t - 1];
                num += s * s;
            }
        }
        if (!(den > 0))
            throw new ArgumentException("samples must not all be equal", nameof(samples));
        return num / den;
    }
}
