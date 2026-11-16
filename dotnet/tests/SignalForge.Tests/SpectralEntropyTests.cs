using Xunit;

namespace SignalForge.Tests;

/// <summary>Spectral entropy (conventions: Spectra, Spectral entropy; ADR 0128).</summary>
public class SpectralEntropyTests
{
    private const double EulerGamma = 0.5772156649015329;
    private static readonly double[] P = [0, 1, 3, 2, 5, 0.5, 0, 4, 1, 0.2];
    private static readonly double[] Ten = [.. Enumerable.Range(0, 10).Select(k => (double)k)];

    private static double[] Axis(int n) => [.. Enumerable.Range(0, n).Select(k => (double)k)];

    [Fact]
    public void ScalingThePsdChangesNothing()
    {
        var want = Spectral.SpectralEntropy(Ten, P);
        var got = Spectral.SpectralEntropy(Ten, [.. P.Select(v => 1e7 * v)]);
        Assert.Equal(want.Entropy, got.Entropy, 1e-12 * Math.Abs(want.Entropy));
        Assert.Equal(want.Normalized, got.Normalized, 1e-12 * want.Normalized);
    }

    [Fact]
    public void StretchingTheAxisScalesTheBandwidth()
    {
        var want = Spectral.SpectralEntropy(Ten, P);
        var got = Spectral.SpectralEntropy([.. Ten.Select(f => 250 * f)], P);
        Assert.Equal(250 * want.EntropyBandwidth, got.EntropyBandwidth, 1e-11 * got.EntropyBandwidth);
        Assert.Equal(want.Normalized, got.Normalized, 1e-11 * want.Normalized);
    }

    [Fact]
    public void ToneOverALowFloorIsNarrow()
    {
        double[] p = [.. Enumerable.Repeat(1e-6, 1000)];
        p[400] = 1;
        Assert.True(Spectral.SpectralEntropy(Axis(1000), p).Normalized < 0.005);
    }

    [Fact]
    public void WhiteNoisePeriodogram()
    {
        const int N = 200_000;
        var rng = new Random(11);
        double[] p = [.. Enumerable.Range(0, N).Select(_ => -Math.Log(1 - rng.NextDouble()))];
        double want = Math.Exp(EulerGamma - 1);
        Assert.Equal(want, Spectral.SpectralEntropy(Axis(N), p).Normalized, 0.01 * want);
    }
}
