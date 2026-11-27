namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Hannah-Kay index of a record of values at least 0, not all 0: the numbers
    /// equivalent (sum s^alpha)^(1/(1 - alpha)) of the shares, exp(-sum s ln s) at
    /// alpha = 1; from 1 to n (conventions: the Hannah-Kay index; ADR 0527).</summary>
    /// <param name="samples">Real values, finite, at least 0, not all 0; at least 1.</param>
    /// <param name="alpha">The order, finite and above 0.</param>
    /// <returns>The Hannah-Kay index, from 1 to n.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double HannahKayIndex(ReadOnlySpan<double> samples, double alpha)
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
        if (!double.IsFinite(alpha) || !(alpha > 0))
            throw new ArgumentOutOfRangeException(nameof(alpha), "alpha must be finite and above 0");
        double acc = 0;
        if (alpha == 1)
        {
            foreach (double v in samples)
            {
                double share = v / total;
                if (share > 0)
                    acc += share * Math.Log(share);
            }
            return Math.Exp(-acc);
        }
        foreach (double v in samples)
            acc += Math.Pow(v / total, alpha);
        return Math.Pow(acc, 1.0 / (1.0 - alpha));
    }
}
