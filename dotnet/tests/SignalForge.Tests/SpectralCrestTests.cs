using Xunit;

namespace SignalForge.Tests;

/// <summary>Spectral crest factor (conventions: Spectra, Spectral crest factor; ADR 0125).</summary>
public class SpectralCrestTests
{
    private static readonly double[] Ten = [.. Enumerable.Range(0, 10).Select(k => (double)k)];
    private static readonly double[] Uneven = [0, 1, 3, 2, 5, 0.5, 0, 4, 1, 0];

    [Fact]
    public void ScalingChangesNothing()
    {
        var want = Spectral.SpectralCrest(Ten, Uneven);
        foreach (double k in new[] { 1e-9, 3.0, 1e9 })
        {
            var got = Spectral.SpectralCrest(Ten, [.. Uneven.Select(v => k * v)]);
            Assert.Equal(want.Crest, got.Crest, 1e-12 * want.Crest);
            Assert.Equal(want.CrestDb, got.CrestDb, 1e-12 * Math.Abs(want.CrestDb));
        }
    }

    [Fact]
    public void ToneInWhiteNoise()
    {
        // Exponential bins of mean 1 (a white-noise periodogram) and one tone bin of height h.
        const int N = 512;
        const double H = 1000;
        var rng = new Random(9);
        double[] p = [.. Enumerable.Range(0, N).Select(_ => -Math.Log(1 - rng.NextDouble()))];
        p[200] = H;
        double[] f = [.. Enumerable.Range(0, N).Select(k => (double)k)];
        var got = Spectral.SpectralCrest(f, p);
        Assert.Equal(H, got.Peak);
        double want = H * N / (N - 1 + H);
        Assert.InRange(got.Crest, want * 0.94, want * 1.06);
    }

    [Fact]
    public void CrestIsNeverBelowOne()
    {
        var rng = new Random(3);
        double[] f = [.. Enumerable.Range(0, 17).Select(k => (double)k)];
        for (int t = 0; t < 50; t++)
        {
            double[] p = [.. Enumerable.Range(0, 17).Select(_ => rng.NextDouble() > 0.3 ? rng.NextDouble() : 0)];
            if (!p.Any(v => v > 0))
                continue;
            var got = Spectral.SpectralCrest(f, p);
            Assert.True(got.Crest >= 1.0);
            Assert.True(got.CrestDb >= -1e-12);
        }
    }

    [Fact]
    public void FlatIsOne()
    {
        var got = Spectral.SpectralCrest(Ten, [.. Enumerable.Repeat(3.5, 10)]);
        Assert.Equal(1.0, got.Crest);
        Assert.Equal(0.0, got.CrestDb);
    }
}
