using Xunit;

namespace SignalForge.Tests;

/// <summary>Spectral variation (conventions: Spectra, Spectral variation; ADR 0131).</summary>
public class SpectralVariationTests
{
    private static readonly double[] Ten = [.. Enumerable.Range(0, 10).Select(k => (double)k)];
    private static readonly double[] A = [0, 1, 3, 2, 5, 0.5, 0, 4, 1, 0.2];
    private static readonly double[] B = [1, 0.5, 2, 4, 1, 0, 2, 3, 0.1, 0.7];

    [Fact]
    public void SwappingTheFramesChangesNothing()
    {
        double want = Spectral.SpectralVariation(Ten, A, B);
        Assert.Equal(want, Spectral.SpectralVariation(Ten, B, A), 1e-13 * want);
    }

    [Fact]
    public void ScalingAFrameChangesNothing()
    {
        double want = Spectral.SpectralVariation(Ten, A, B, (1.25, 8.0));
        double got = Spectral.SpectralVariation(Ten, [.. A.Select(v => 3e5 * v)], [.. B.Select(v => 0.01 * v)], (1.25, 8.0));
        Assert.Equal(want, got, 1e-12 * want);
    }

    [Fact]
    public void RandomFramesStayInRange()
    {
        var rng = new Random(5);
        double[] Frame() => [.. Enumerable.Range(0, 10).Select(_ => -Math.Log(1 - rng.NextDouble()))];
        for (int i = 0; i < 50; i++)
        {
            double v = Spectral.SpectralVariation(Ten, Frame(), Frame());
            Assert.InRange(v, 0.0, 1.0);
        }
    }
}
