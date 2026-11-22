namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Hill number of order <paramref name="order"/> of a record of values at
    /// least 0, not all 0: the effective number of kinds, (sum p^q)^(1/(1-q)) over the shares
    /// above 0 (conventions: the Hill number; ADR 0563).</summary>
    /// <param name="samples">Real values, finite, at least 0, not all 0; at least 1.</param>
    /// <param name="order">The order q, finite and at least 0.</param>
    /// <returns>The Hill number, from 1 to the count of values above 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double HillNumber(ReadOnlySpan<double> samples, double order)
    {
        if (!double.IsFinite(order) || !(order >= 0))
            throw new ArgumentException("order must be finite and at least 0", nameof(order));
        int n = samples.Length;
        if (n < 1)
            throw new ArgumentException("samples must not be empty", nameof(samples));
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
        List<double> shares = new();
        foreach (double v in samples)
        {
            if (v > 0)
                shares.Add(v / total);
        }
        double q = order;
        if (q == 0)
            return shares.Count;
        if (q == 1)
        {
            double acc = 0;
            foreach (double p in shares)
                acc += p * Math.Log(p);
            return Math.Exp(-acc);
        }
        if (Math.Abs(q - 1.0) < 0.5)
        {
            double s = 0;
            foreach (double p in shares)
                s += p * Spectral.ExpM1((q - 1.0) * Math.Log(p));
            return Math.Exp(Spectral.LogP1(s) / (1.0 - q));
        }
        double m = 0;
        foreach (double p in shares)
            m = Math.Max(m, p);
        double t = 0;
        foreach (double p in shares)
            t += Math.Pow(p / m, q);
        return Math.Exp(((q * Math.Log(m)) + Math.Log(t)) / (1.0 - q));
    }
}
