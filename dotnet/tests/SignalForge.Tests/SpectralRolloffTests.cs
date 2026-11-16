using Xunit;

namespace SignalForge.Tests;

/// <summary>Spectral rolloff (conventions: Spectra, Spectral rolloff; ADR 0124).</summary>
public class SpectralRolloffTests
{
    private static readonly double[] Ten = [.. Enumerable.Range(0, 10).Select(k => (double)k)];
    private static readonly double[] Ones = [.. Enumerable.Repeat(1.0, 10)];
    private static readonly double[] Uneven = [0, 1, 3, 2, 5, 0.5, 0, 4, 1, 0];
    private static readonly double[] Symmetric = [1, 2, 5, 2, 1];
    private static readonly double[] SymmetricAxis = [10, 11, 12, 13, 14];

    [Theory]
    [InlineData(0.01)]
    [InlineData(0.1)]
    [InlineData(0.25)]
    [InlineData(0.5)]
    [InlineData(0.85)]
    [InlineData(0.95)]
    [InlineData(1.0)]
    public void FlatPsdGivesTheLinearShare(double q) =>
        Assert.Equal(-0.5 + q * 10, Spectral.SpectralRolloff(Ten, Ones, q), 1e-12);

    [Fact]
    public void ScalingChangesNothing()
    {
        double want = Spectral.SpectralRolloff(Ten, Uneven, 0.7);
        foreach (double k in new[] { 1e-9, 3.0, 1e9 })
        {
            double got = Spectral.SpectralRolloff(Ten, [.. Uneven.Select(v => k * v)], 0.7);
            Assert.Equal(want, got, 1e-12 * Math.Abs(want));
        }
    }

    [Fact]
    public void RolloffRisesWithTheFraction()
    {
        var rng = new Random(5);
        double[] f = [.. Enumerable.Range(0, 64).Select(k => (double)k)];
        double[] p = [.. Enumerable.Range(0, 64).Select(k => k % 3 != 0 ? rng.NextDouble() : 0)];
        double previous = double.NegativeInfinity;
        for (int i = 1; i <= 100; i++)
        {
            double got = Spectral.SpectralRolloff(f, p, i / 100.0);
            Assert.True(got >= previous);
            previous = got;
        }
    }

    [Fact]
    public void SymmetricPsdHalvesAtItsCentre() =>
        Assert.Equal(12.0, Spectral.SpectralRolloff(SymmetricAxis, Symmetric, 0.5), 1e-12);

    [Fact]
    public void BandCutsBins() =>
        Assert.Equal(3.0, Spectral.SpectralRolloff(Ten, Ones, 0.5, band: (2.25, 3.75)), 1e-12);
}
