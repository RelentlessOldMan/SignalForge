using Xunit;

namespace SignalForge.Tests;

/// <summary>Spectral skewness and kurtosis (conventions: Spectra, Spectral skewness and kurtosis;
/// ADR 0126).</summary>
public class SpectralShapeTests
{
    private static readonly double[] P = [0, 1, 3, 2, 5, 0.5, 0, 4, 1, 0.2];
    private static readonly double[] Ten = [.. Enumerable.Range(0, 10).Select(k => (double)k)];

    [Fact]
    public void MirroringFlipsTheSkewness()
    {
        var got = Spectral.SpectralShape(Ten, P);
        var mirrored = Spectral.SpectralShape(Ten, [.. P.Reverse()]);
        Assert.Equal(-got.Skewness, mirrored.Skewness, 1e-11 * Math.Abs(got.Skewness));
        Assert.Equal(got.Kurtosis, mirrored.Kurtosis, 1e-11 * got.Kurtosis);
    }

    [Theory]
    [InlineData(1e3, 1.0)]
    [InlineData(-50.0, 0.01)]
    [InlineData(7.0, 250.0)]
    public void AxisShiftAndStretchChangeNothing(double shift, double stretch)
    {
        var want = Spectral.SpectralShape(Ten, P);
        var got = Spectral.SpectralShape([.. Ten.Select(f => shift + stretch * f)], P);
        Assert.Equal(want.Skewness, got.Skewness, 1e-9 * Math.Abs(want.Skewness));
        Assert.Equal(want.Kurtosis, got.Kurtosis, 1e-9 * want.Kurtosis);
    }

    [Fact]
    public void GaussianPsd()
    {
        const double Sigma = 40;
        double[] f = [.. Enumerable.Range(-400, 801).Select(k => (double)k)];
        double[] p = [.. f.Select(v => Math.Exp(-v * v / (2 * Sigma * Sigma)))];
        var got = Spectral.SpectralShape(f, p);
        Assert.Equal(0.0, got.Skewness, 1e-12);
        // A step density adds a bin's own uniform spread: m2 = s² + 1/12, m4 = 3s⁴ + s²/2 + 1/80.
        double m2 = Sigma * Sigma + 1.0 / 12, m4 = 3 * Math.Pow(Sigma, 4) + Sigma * Sigma / 2 + 1.0 / 80;
        Assert.Equal(m4 / (m2 * m2), got.Kurtosis, 1e-6 * got.Kurtosis);
    }

    [Fact]
    public void FlatBandIsUniform()
    {
        var got = Spectral.SpectralShape(Ten, [.. Enumerable.Repeat(1.0, 10)], band: (1.3, 6.1));
        Assert.Equal(0.0, got.Skewness, 1e-12);
        Assert.Equal(1.8, got.Kurtosis, 1e-12);
    }
}
