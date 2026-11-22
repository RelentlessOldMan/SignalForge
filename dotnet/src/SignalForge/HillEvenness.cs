namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Hill evenness of order <paramref name="order"/> of a record of values at
    /// least 0, not all 0: the Hill number over the count of values above 0, from 1/K to 1
    /// (conventions: Hill evenness; ADR 0564).</summary>
    /// <param name="samples">Real values, finite, at least 0, not all 0; at least 1.</param>
    /// <param name="order">The order q, finite and at least 0.</param>
    /// <returns>Hill evenness, from 1/K to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double HillEvenness(ReadOnlySpan<double> samples, double order)
    {
        double d = HillNumber(samples, order);
        int k = 0;
        foreach (double v in samples)
        {
            if (v > 0)
                k++;
        }
        return d / k;
    }
}
