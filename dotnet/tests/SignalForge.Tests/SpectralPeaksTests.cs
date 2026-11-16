using Xunit;

namespace SignalForge.Tests;

/// <summary>Spectral peaks (conventions: Spectra, Spectral peaks; ADR 0135).</summary>
public class SpectralPeaksTests
{
    private static readonly double[] Twelve = [.. Enumerable.Range(0, 12).Select(k => (double)k)];
    private static readonly double[] P = [0.5, 3, 1, 4, 4, 2, 6, 0.2, 1, 0.3, 2.5, 1.5];

    [Fact]
    public void ScalingScalesHeightsAndProminences()
    {
        var baseline = Spectral.SpectralPeaks(Twelve, P);
        var scaled = Spectral.SpectralPeaks(Twelve, [.. P.Select(v => 8 * v)]);
        Assert.Equal(baseline.Select(p => p.Index), scaled.Select(p => p.Index));
        for (int k = 0; k < baseline.Count; k++)
        {
            Assert.Equal(8 * baseline[k].Height, scaled[k].Height);
            Assert.Equal(8 * baseline[k].Prominence, scaled[k].Prominence);
        }
    }

    [Fact]
    public void HeightIsAtLeastTheProminence()
    {
        var got = Spectral.SpectralPeaks(Twelve, P);
        Assert.NotEmpty(got);
        Assert.All(got, p => Assert.InRange(p.Prominence, double.Epsilon, p.Height));
    }

    [Fact]
    public void ThresholdKeepsASubset()
    {
        var every = Spectral.SpectralPeaks(Twelve, P);
        var kept = Spectral.SpectralPeaks(Twelve, P, 2.0);
        Assert.Equal(every.Where(p => p.Prominence >= 2.0), kept);
    }

    [Fact]
    public void TonesInNoiseAreTheMostProminent()
    {
        var rng = new Random(135);
        double[] f = [.. Enumerable.Range(0, 256).Select(k => 10.0 * k)];
        double[] psd = [.. Enumerable.Range(0, 256).Select(_ => -Math.Log(1 - rng.NextDouble()))];
        psd[40] += 100;
        psd[170] += 100;
        var top = Spectral.SpectralPeaks(f, psd).OrderByDescending(p => p.Prominence).Take(2).ToList();
        Assert.Equal([40, 170], top.Select(p => p.Index).Order());
        Assert.Equal([400.0, 1700.0], top.Select(p => p.Frequency).Order());
    }

    [Theory]
    [InlineData(-0.5)]
    [InlineData(double.NaN)]
    [InlineData(double.PositiveInfinity)]
    public void BadFloorIsRejected(double floor) =>
        Assert.ThrowsAny<ArgumentException>(() => Spectral.SpectralPeaks(Twelve, P, floor));
}
