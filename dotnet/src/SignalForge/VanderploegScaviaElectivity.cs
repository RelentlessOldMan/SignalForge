namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Vanderploeg and Scavia's relativized electivity of the record of use
    /// <paramref name="x"/> against the record of availability <paramref name="available"/>,
    /// records as for <see cref="ManlyAlpha"/>: (a - 1/n)/(a + 1/n) for each kind with a
    /// Manly's alpha, from -1 to 1 (conventions: Vanderploeg and Scavia's relativized
    /// electivity; ADR 0605).</summary>
    /// <param name="x">The record of use, finite, at least 0, with a value above 0.</param>
    /// <param name="available">The record of availability, finite and above 0, the same
    /// length as x.</param>
    /// <returns>The relativized electivity for each kind.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, an availability share
    /// underflows to 0, or the sum of the ratios overflows.</exception>
    public static double[] VanderploegScaviaElectivity(ReadOnlySpan<double> x, ReadOnlySpan<double> available)
    {
        double[] result = ManlyAlpha(x, available);
        double e = 1.0 / result.Length;
        for (int i = 0; i < result.Length; i++)
            result[i] = Math.Min(Math.Max((result[i] - e) / (result[i] + e), -1.0), 1.0);
        return result;
    }
}
