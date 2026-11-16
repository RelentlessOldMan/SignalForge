using Xunit;

namespace SignalForge.Tests;

/// <summary>Harmonic centroid and spread (conventions: Spectra, Harmonic centroid; ADR 0145).</summary>
public class HarmonicCentroidTests
{
    private static readonly double[] Tones = [101, 199, 302, 405, 150];
    private static readonly double[] Heights = [5, 3, 2, 1, 7];
    private static readonly int[] Orders = [1, 2, 3, 4, 0];

    [Fact]
    public void ScalingHeightsLeavesItUnchanged()
    {
        var a = Spectral.HarmonicCentroid(Tones, Heights, Orders);
        var b = Spectral.HarmonicCentroid(Tones, [.. Heights.Select(h => 6 * h)], Orders);
        Assert.Equal(a.Centroid, b.Centroid, 1e-12 * a.Centroid);
        Assert.Equal(a.Spread, b.Spread, 1e-12 * a.Spread);
    }

    [Fact]
    public void ScalingFrequenciesScalesBoth()
    {
        var a = Spectral.HarmonicCentroid(Tones, Heights, Orders);
        var b = Spectral.HarmonicCentroid([.. Tones.Select(t => 2.5 * t)], Heights, Orders);
        Assert.Equal(2.5 * a.Centroid, b.Centroid, 1e-12 * b.Centroid);
        Assert.Equal(2.5 * a.Spread, b.Spread, 1e-12 * b.Spread);
    }
}
