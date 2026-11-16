using Xunit;

namespace SignalForge.Tests;

/// <summary>Spectral contrast (conventions: Spectra, Spectral contrast; ADR 0133).</summary>
public class SpectralContrastTests
{
    private static readonly double[] Ten = [.. Enumerable.Range(0, 10).Select(k => (double)k)];
    private static readonly double[] P = [3, 1, 3, 2, 5, 0.5, 0.1, 4, 1, 0.2];

    [Fact]
    public void ScalingScalesPeakAndValley()
    {
        var want = Spectral.SpectralContrast(Ten, P, (0.25, 8.6));
        var got = Spectral.SpectralContrast(Ten, [.. P.Select(v => 1e3 * v)], (0.25, 8.6));
        Assert.Equal(1e3 * want.Peak, got.Peak, 1e-12 * got.Peak);
        Assert.Equal(1e3 * want.Valley, got.Valley, 1e-12 * got.Valley);
        Assert.Equal(want.ContrastDb, got.ContrastDb, 1e-12 * want.ContrastDb);
    }

    [Fact]
    public void HalfSplitGivesTheMean()
    {
        var got = Spectral.SpectralContrast(Ten, P, fraction: 0.5);
        Assert.Equal(P.Average(), (got.Peak + got.Valley) / 2, 1e-12 * P.Average());
    }

    [Fact]
    public void ZeroValleyIsInfinite()
    {
        var got = Spectral.SpectralContrast(Ten, [.. P.Select(v => v < 0.5 ? 0 : v)]);
        Assert.Equal(0, got.Valley);
        Assert.Equal(double.PositiveInfinity, got.ContrastDb);
    }

    [Fact]
    public void ToneOverAFloor()
    {
        double[] p = [.. Enumerable.Repeat(1e-4, 1000)];
        for (int k = 300; k < 310; k++)
            p[k] = 1;
        var got = Spectral.SpectralContrast([.. Enumerable.Range(0, 1000).Select(k => (double)k)], p, fraction: 0.01);
        Assert.Equal(40.0, got.ContrastDb, 1e-12 * 40);
    }
}
