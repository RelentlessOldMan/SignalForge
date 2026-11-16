using Xunit;

namespace SignalForge.Tests;

/// <summary>Harmonic spectral deviation (conventions: Spectra, Harmonic deviation; ADR 0144).</summary>
public class HarmonicDeviationTests
{
    private static readonly double[] Heights = [5, 3, 2, 1, 0.5, 0.25, 7];
    private static readonly int[] Orders = [1, 2, 3, 4, 5, 9, 0];

    [Fact]
    public void ScalingHeightsLeavesItUnchanged()
    {
        double a = Spectral.HarmonicDeviation(Heights, Orders);
        double b = Spectral.HarmonicDeviation([.. Heights.Select(h => 6 * h)], Orders);
        Assert.Equal(a, b, 1e-12 * a);
    }

    [Fact]
    public void LinearFallDeviatesOnlyAtTheEnds()
    {
        // Amplitudes 12, 11, ..., 1: each inner envelope equals its amplitude, and each end's
        // envelope is half a step off, so the deviation is (1/2 + 1/2) / 78.
        int[] m = [.. Enumerable.Range(1, 12)];
        double got = Spectral.HarmonicDeviation([.. m.Select(k => Math.Pow(13 - k, 2))], m);
        Assert.Equal(1.0 / 78, got, 1e-14);
    }
}
