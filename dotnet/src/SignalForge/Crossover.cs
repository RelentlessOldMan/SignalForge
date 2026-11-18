namespace SignalForge;

/// <summary>The low and high bands of a crossover, each a cascade of second-order sections
/// <c>[b0, b1, b2, a0, a1, a2]</c> (conventions: Linkwitz-Riley crossover; ADR 0284).</summary>
/// <param name="Low">The low band's sections.</param>
/// <param name="High">The high band's sections.</param>
public sealed record Crossover(double[][] Low, double[][] High);

public static partial class Dsp
{
    /// <summary>Linkwitz-Riley crossover of even <paramref name="order"/>: each band a squared
    /// Butterworth of half the order, the two summing to an all-pass (conventions: Linkwitz-Riley
    /// crossover; ADR 0284).</summary>
    /// <param name="order">The crossover order, even, from 2 to 2000.</param>
    /// <param name="cutoff">The crossover frequency, Hz, between 0 and sampleRate/2.</param>
    /// <param name="sampleRate">The sample rate, Hz.</param>
    /// <returns>The low and high bands.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Crossover LinkwitzRiley(int order, double cutoff, double sampleRate)
    {
        if (order < 2 || order > 2000 || order % 2 != 0)
            throw new ArgumentOutOfRangeException(nameof(order), "order must be even, from 2 to 2000");
        double[][] lo = ButterworthLowpass(order / 2, cutoff, sampleRate);
        double[][] hi = ButterworthHighpass(order / 2, cutoff, sampleRate);
        double[][] low = [.. lo.Select(r => (double[])r.Clone()), .. lo.Select(r => (double[])r.Clone())];
        double[][] high = [.. hi.Select(r => (double[])r.Clone()), .. hi.Select(r => (double[])r.Clone())];
        if (order / 2 % 2 == 1)
        {
            for (int i = 0; i < 3; i++)
                high[0][i] = -high[0][i];
        }
        return new Crossover(low, high);
    }
}
