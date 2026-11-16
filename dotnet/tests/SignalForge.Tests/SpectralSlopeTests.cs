using Xunit;

namespace SignalForge.Tests;

/// <summary>Spectral slope (conventions: Spectra, Spectral slope; ADR 0127).</summary>
public class SpectralSlopeTests
{
    private static readonly double[] P = [0, 1, 3, 2, 5, 0.5, 0, 4, 1, 0.2];
    private static readonly double[] Ten = [.. Enumerable.Range(0, 10).Select(k => (double)k)];

    private static double[] Axis(int m) => [.. Enumerable.Range(0, m).Select(k => (double)k)];

    [Theory]
    [InlineData(2)]
    [InlineData(3)]
    [InlineData(7)]
    [InlineData(64)]
    [InlineData(501)]
    public void ASampledLineGivesTheStaircaseSlope(int m)
    {
        double[] f = Axis(m);
        var got = Spectral.SpectralSlope(f, [.. f.Select(v => 5.0 + 0.3 * v)]);
        double want = 0.3 * (1 - 1.0 / ((double)m * m));
        Assert.Equal(want, got.Slope, 1e-11 * want);
        Assert.Equal(5.0 + 0.3 * (m - 1) / 2, got.Level, 1e-12 * got.Level);
    }

    [Fact]
    public void LevelTimesWidthIsTheBandPower()
    {
        var got = Spectral.SpectralSlope(Ten, P, band: (1.2, 7.9));
        double power = Spectral.SpectralMoments(Ten, P, band: (1.2, 7.9)).Power;
        Assert.Equal(power, got.Level * (7.9 - 1.2), 1e-12 * power);
        Assert.Equal(4.55, got.Center, 1e-12);
    }

    [Fact]
    public void MirroringNegatesTheSlope()
    {
        var got = Spectral.SpectralSlope(Ten, P);
        var mirrored = Spectral.SpectralSlope(Ten, [.. P.Reverse()]);
        Assert.Equal(-got.Slope, mirrored.Slope, 1e-12 * Math.Abs(got.Slope));
        Assert.Equal(got.Level, mirrored.Level, 1e-12 * got.Level);
    }

    [Fact]
    public void ShiftingTheAxisChangesOnlyTheCenter()
    {
        var want = Spectral.SpectralSlope(Ten, P);
        var got = Spectral.SpectralSlope([.. Ten.Select(f => f + 1e4)], P);
        Assert.Equal(want.Center + 1e4, got.Center, 1e-9);
        Assert.Equal(want.Level, got.Level, 1e-12 * want.Level);
        Assert.Equal(want.Slope, got.Slope, 1e-8 * Math.Abs(want.Slope));
    }

    [Fact]
    public void DbOfAnExponentialPsd()
    {
        // 10 log10 of 10^(-0.05 f) is -0.5 f dB: a dB line, flattened by the staircase.
        const int M = 40;
        double[] f = Axis(M);
        var got = Spectral.SpectralSlope(f, [.. f.Select(v => Math.Pow(10, -0.05 * v))], db: true);
        double want = -0.5 * (1 - 1.0 / (M * M));
        Assert.Equal(want, got.Slope, 1e-11 * Math.Abs(want));
    }
}
