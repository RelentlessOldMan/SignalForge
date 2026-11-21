namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Atkinson index of a record of positive values with inequality aversion
    /// <paramref name="epsilon"/> at least 0: one less the power mean of order 1 - epsilon
    /// over the mean, from 0 to below 1 (conventions: the Atkinson index; ADR 0515).</summary>
    /// <param name="samples">Real values, finite, greater than 0; at least 1.</param>
    /// <param name="epsilon">The inequality aversion, finite, at least 0.</param>
    /// <returns>The Atkinson index, from 0 to below 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double AtkinsonIndex(ReadOnlySpan<double> samples, double epsilon)
    {
        if (!double.IsFinite(epsilon) || !(epsilon >= 0))
            throw new ArgumentException("epsilon must be finite and at least 0", nameof(epsilon));
        int n = samples.Length;
        if (n < 1)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        double total = 0;
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            if (!(v > 0))
                throw new ArgumentException("samples must be greater than 0", nameof(samples));
            total += v;
        }
        double mean = total / n;
        double sum = 0;
        if (epsilon == 1)
        {
            foreach (double v in samples)
                sum += Math.Log(v / mean);
            return 1.0 - Math.Exp(sum / n);
        }
        double p = 1.0 - epsilon;
        foreach (double v in samples)
            sum += Math.Pow(v / mean, p);
        return 1.0 - Math.Pow(sum / n, 1.0 / p);
    }
}
