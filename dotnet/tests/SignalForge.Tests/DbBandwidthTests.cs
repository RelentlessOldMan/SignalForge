using Xunit;

namespace SignalForge.Tests;

/// <summary>x dB bandwidth (conventions: Spectra, x dB bandwidth; ADR 0122).</summary>
public class DbBandwidthTests
{
    private static double[] Axis(int n, double step = 1, double start = 0) => [.. Enumerable.Range(0, n).Select(k => start + k * step)];

    [Theory]
    [InlineData(3.0)]
    [InlineData(6.0)]
    [InlineData(26.0)]
    public void GaussianPsd(double drop)
    {
        const double Sigma = 2.5;
        double[] f = Axis(80001, 0.001, -40);
        double[] p = [.. f.Select(v => 7 * Math.Exp(-(v - 0.75) * (v - 0.75) / (2 * Sigma * Sigma)))];
        var r = Spectral.DbBandwidth(f, p, drop);
        // exp(−u²/(2σ²)) = 10^(−drop/10) at u = σ·sqrt(drop·ln 10 / 5)
        double u = Sigma * Math.Sqrt(drop * Math.Log(10) / 5);
        Assert.Equal(2 * u, r.Bandwidth, 2 * u * 1e-6);
        Assert.Equal(u, r.Upper - 0.75, u * 1e-6);
        Assert.Equal(0.75, (r.Lower + r.Upper) / 2, 1e-9);
        Assert.Equal(0.75, r.PeakFrequency, 1e-9);
    }

    [Fact]
    public void RectangleIsItsWidthWithinABin()
    {
        double[] f = Axis(200, 0.25);
        double[] p = [.. f.Select(v => v >= 10 && v <= 20 ? 1.0 : 1e-6)];
        var r = Spectral.DbBandwidth(f, p, 20.0);
        const double Width = 41 * 0.25; // bins 10 ... 20 Hz, each 0.25 Hz wide
        Assert.InRange(r.Bandwidth, Width - 0.25, Width + 0.25);
        // the bin at 9.75 is at 1e-6, the one at 10 at 1: the 0.01 crossing lies between
        double want = 9.75 + 0.25 * (0.01 - 1e-6) / (1 - 1e-6);
        Assert.Equal(want, r.Lower, want * 1e-12);
    }

    [Fact]
    public void ScalingChangesOnlyThePeak()
    {
        var rng = new Random(122);
        double[] f = Axis(101);
        double[] p = [.. f.Select(v => Math.Exp(-(v - 50) * (v - 50) / 200) * (0.9 + 0.1 * rng.NextDouble()))];
        var a = Spectral.DbBandwidth(f, p, 6.0);
        var b = Spectral.DbBandwidth(f, [.. p.Select(v => 1e9 * v)], 6.0);
        Assert.Equal(1e9 * a.PeakPsd, b.PeakPsd, 1e9 * a.PeakPsd * 1e-15);
        Assert.Equal(a.Lower, b.Lower, Math.Abs(a.Lower) * 1e-12);
        Assert.Equal(a.Upper, b.Upper, Math.Abs(a.Upper) * 1e-12);
    }

    [Fact]
    public void TheWalkStopsAtTheFirstDip()
    {
        double[] p = [0, 8, 1, 8, 10, 8, 1, 8, 0];
        var r = Spectral.DbBandwidth(Axis(9), p, 3.0);
        Assert.InRange(r.Lower, 2, 3);
        Assert.InRange(r.Upper, 5, 6);
    }
}
