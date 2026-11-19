namespace SignalForge;

/// <summary>The number of strict local extrema and its z-score against an i.i.d. record
/// (conventions: Turning point test; ADR 0360).</summary>
/// <param name="Count">The number of samples strictly above or strictly below both
/// neighbours.</param>
/// <param name="Z">The z-score of <paramref name="Count"/> against the i.i.d. mean
/// <c>2(N − 2)/3</c> and variance <c>(16N − 29)/90</c>.</param>
public sealed record TurningPoints(int Count, double Z);

public static partial class Measurements
{
    /// <summary>The turning point test: the number of samples strictly above or below both
    /// neighbours, and its z-score against an i.i.d. record (conventions: Turning point test;
    /// ADR 0360).</summary>
    /// <param name="samples">Real samples, finite, at least 3.</param>
    /// <returns>The count and its z-score.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static TurningPoints TurningPoints(ReadOnlySpan<double> samples)
    {
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        int n = samples.Length;
        if (n < 3)
            throw new ArgumentException("samples must have at least 3 values", nameof(samples));
        int k = 0;
        for (int i = 1; i < n - 1; i++)
        {
            double a = samples[i - 1], b = samples[i], c = samples[i + 1];
            if ((b > a && b > c) || (b < a && b < c))
                k++;
        }
        double z = (k - 2.0 * (n - 2) / 3) / Math.Sqrt((16.0 * n - 29) / 90);
        return new TurningPoints(k, z);
    }
}
