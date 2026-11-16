using Xunit;

namespace SignalForge.Tests;

/// <summary>Spectral centroid and RMS bandwidth (conventions: Spectra, Spectral centroid and RMS
/// bandwidth; ADR 0121).</summary>
public class SpectralMomentsTests
{
    private static double[] Axis(int n, double step = 1) => [.. Enumerable.Range(0, n).Select(k => k * step)];

    private static void Near(double want, double got, double rel) => Assert.Equal(want, got, Math.Abs(want) * rel);

    [Theory]
    [InlineData(10, 30)]
    [InlineData(0, 99)]
    [InlineData(40, 41)]
    public void RectangleIsWidthOverRootTwelve(int lo, int hi)
    {
        double[] f = Axis(100, 0.5);
        double[] p = [.. Enumerable.Range(0, 100).Select(k => k >= lo && k <= hi ? 3.0 : 0.0)];
        var r = Spectral.SpectralMoments(f, p);
        double width = (hi - lo + 1) * 0.5;
        Near(3 * width, r.Power, 1e-12);
        Near((f[lo] + f[hi]) / 2, r.Centroid, 1e-12);
        Near(width / Math.Sqrt(12), r.RmsBandwidth, 1e-12);
    }

    [Fact]
    public void CutBandOnAFlatPsd()
    {
        double[] ones = [.. Enumerable.Repeat(1.0, 64)];
        var r = Spectral.SpectralMoments(Axis(64), ones, (10.3, 40.8));
        Near(30.5, r.Power, 1e-12);
        Near((10.3 + 40.8) / 2, r.Centroid, 1e-12);
        Near(30.5 / Math.Sqrt(12), r.RmsBandwidth, 1e-12);
    }

    [Fact]
    public void GaussianPsdGivesItsSigma()
    {
        const double Sigma = 4.0, Delta = 100.0 / 20000;
        double[] f = [.. Enumerable.Range(0, 20001).Select(k => -50 + k * Delta)];
        double[] p = [.. f.Select(v => Math.Exp(-(v - 1.25) * (v - 1.25) / (2 * Sigma * Sigma)))];
        var r = Spectral.SpectralMoments(f, p);
        Assert.Equal(1.25, r.Centroid, 1e-9);
        // the step density adds Δ²/12 to the variance
        Near(Math.Sqrt(Sigma * Sigma + Delta * Delta / 12), r.RmsBandwidth, 1e-9);
    }

    [Fact]
    public void ShiftingTheAxisShiftsOnlyTheCentroid()
    {
        var rng = new Random(121);
        double[] p = [.. Enumerable.Range(0, 80).Select(_ => rng.NextDouble())];
        double[] f = Axis(80);
        var a = Spectral.SpectralMoments(f, p);
        var b = Spectral.SpectralMoments([.. f.Select(v => v + 1e6)], p);
        Assert.Equal(a.Centroid, b.Centroid - 1e6, 1e-8);
        Near(a.RmsBandwidth, b.RmsBandwidth, 1e-9);
        Near(a.Power, b.Power, 1e-12);
    }

    [Fact]
    public void PowerMatchesChannelPower()
    {
        var rng = new Random(1210);
        double[] p = [.. Enumerable.Range(0, 40).Select(_ => rng.NextDouble())];
        double[] f = Axis(40);
        Near(Spectral.ChannelPower(f, p, 3.7, 22.2), Spectral.SpectralMoments(f, p, (3.7, 22.2)).Power, 1e-12);
    }
}
