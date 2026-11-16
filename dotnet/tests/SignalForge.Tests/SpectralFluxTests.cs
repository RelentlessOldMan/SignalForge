using Xunit;

namespace SignalForge.Tests;

/// <summary>Spectral flux (conventions: Spectra, Spectral flux; ADR 0129).</summary>
public class SpectralFluxTests
{
    private static readonly double[] Ten = [.. Enumerable.Range(0, 10).Select(k => (double)k)];
    private static readonly double[] A = [0, 1, 3, 2, 5, 0.5, 0, 4, 1, 0.2];
    private static readonly double[] B = [1, 0.5, 2, 4, 1, 0, 2, 3, 0.1, 0.7];

    [Fact]
    public void UnrectifiedIsSymmetric()
    {
        double there = Spectral.SpectralFlux(Ten, A, B, rectify: false);
        double back = Spectral.SpectralFlux(Ten, B, A, rectify: false);
        Assert.Equal(there, back, 1e-13 * there);
    }

    [Fact]
    public void RisesAndFallsAddInSquares()
    {
        double up = Spectral.SpectralFlux(Ten, A, B);
        double down = Spectral.SpectralFlux(Ten, B, A);
        double both = Spectral.SpectralFlux(Ten, A, B, rectify: false);
        Assert.Equal(both * both, up * up + down * down, 1e-12 * both * both);
    }

    [Fact]
    public void ScalingAFrameChangesNothingNormalized()
    {
        double want = Spectral.SpectralFlux(Ten, A, B, (1.25, 8.0));
        double got = Spectral.SpectralFlux(Ten, [.. A.Select(v => 3e5 * v)], [.. B.Select(v => 0.01 * v)], (1.25, 8.0));
        Assert.Equal(want, got, 1e-12 * want);
    }

    [Fact]
    public void LengthsMustMatch() =>
        Assert.ThrowsAny<ArgumentException>(() => Spectral.SpectralFlux(Ten, A, B.AsSpan(0, 9)));
}
