namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Renyi evenness of order <paramref name="order"/> of a record of values at
    /// least 0, at least two of them above 0: the Renyi diversity of counts over ln K, from
    /// 0 to 1 (conventions: Renyi evenness; ADR 0567).</summary>
    /// <param name="samples">Real values, finite, at least 0, at least two above 0.</param>
    /// <param name="order">The order q, finite and at least 0.</param>
    /// <returns>Renyi evenness, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double RenyiEvenness(ReadOnlySpan<double> samples, double order)
    {
        double h = RenyiDiversity(samples, order);
        int k = 0;
        foreach (double v in samples)
        {
            if (v > 0)
                k++;
        }
        if (k < 2)
            throw new ArgumentException("samples must have at least two values above 0", nameof(samples));
        return h / Math.Log(k);
    }
}
