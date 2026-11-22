namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Alatalo's evenness of a record of values at least 0 with at least 2 above 0:
    /// the Hill number of order 2 less 1 over that of order 1 less 1, above 0 and at most 1
    /// (conventions: Alatalo's evenness; ADR 0537).</summary>
    /// <param name="samples">Real values, finite, at least 0, at least 2 above 0.</param>
    /// <returns>Alatalo's evenness, above 0 and at most 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double AlataloEvenness(ReadOnlySpan<double> samples)
    {
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
        double sq = 0;
        double ent = 0;
        int positive = 0;
        foreach (double v in samples)
        {
            double share = v / total;
            sq += share * share;
            if (share > 0)
            {
                ent += share * Math.Log(share);
                positive++;
            }
        }
        if (positive < 2)
            throw new ArgumentException("samples must have at least 2 values above 0", nameof(samples));
        return ((1.0 / sq) - 1.0) / (Math.Exp(-ent) - 1.0);
    }
}
