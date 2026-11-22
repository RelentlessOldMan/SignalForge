namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Tsallis evenness of order <paramref name="order"/> of a record of values at
    /// least 0, at least two of them above 0: the Tsallis diversity of counts over its value
    /// for K equal shares, from 0 to 1 (conventions: Tsallis evenness; ADR 0569).</summary>
    /// <param name="samples">Real values, finite, at least 0, at least two above 0.</param>
    /// <param name="order">The order q, finite and at least 0.</param>
    /// <returns>Tsallis evenness, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double TsallisEvenness(ReadOnlySpan<double> samples, double order)
    {
        double d = TsallisDiversity(samples, order);
        int k = 0;
        foreach (double v in samples)
        {
            if (v > 0)
                k++;
        }
        if (k < 2)
            throw new ArgumentException("samples must have at least two values above 0", nameof(samples));
        if (order == 1)
            return d / Math.Log(k);
        return d / (-Spectral.ExpM1((1.0 - order) * Math.Log(k)) / (order - 1.0));
    }
}
