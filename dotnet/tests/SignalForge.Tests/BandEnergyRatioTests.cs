using Xunit;

namespace SignalForge.Tests;

/// <summary>Band energy ratio (conventions: Spectra, Band energy ratio; ADR 0134).</summary>
public class BandEnergyRatioTests
{
    private static readonly double[] Ten = [.. Enumerable.Range(0, 10).Select(k => (double)k)];
    private static readonly double[] P = [3, 1, 3, 2, 5, 0.5, 0.1, 4, 1, 0.2];

    [Fact]
    public void LowAndHighAddToTheChannelPower()
    {
        var got = Spectral.BandEnergyRatio(Ten, P, 3.7, (0.25, 8.6));
        double want = Spectral.ChannelPower(Ten, P, 0.25, 8.6);
        Assert.Equal(want, got.Low + got.High, 1e-12 * want);
    }

    [Fact]
    public void MirroringInvertsTheRatio()
    {
        var there = Spectral.BandEnergyRatio(Ten, P, 4.5);
        var back = Spectral.BandEnergyRatio(Ten, [.. P.Reverse()], 4.5);
        Assert.Equal(1 / there.Ratio, back.Ratio, 1e-12 * back.Ratio);
        Assert.Equal(-there.RatioDb, back.RatioDb, 1e-12 * Math.Abs(back.RatioDb));
    }

    [Fact]
    public void NoLowPowerIsInfinite()
    {
        var got = Spectral.BandEnergyRatio(Ten, [.. P.Select((v, k) => k < 5 ? 0 : v)], 4.5);
        Assert.Equal(0, got.Low);
        Assert.Equal(double.PositiveInfinity, got.Ratio);
        Assert.Equal(double.PositiveInfinity, got.RatioDb);
    }

    [Fact]
    public void NoHighPowerIsZero()
    {
        var got = Spectral.BandEnergyRatio(Ten, [.. P.Select((v, k) => k < 5 ? v : 0)], 4.5);
        Assert.Equal(0, got.Ratio);
        Assert.Equal(double.NegativeInfinity, got.RatioDb);
    }
}
