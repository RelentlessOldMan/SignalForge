using Xunit;

namespace SignalForge.Tests;

/// <summary>Lomb-Scargle periodogram (conventions: Spectra, Lomb-Scargle periodogram; ADR 0059).</summary>
public class LombScargleTests
{
    private static readonly Random Rng = new(59);
    private static readonly double[] T = [.. Enumerable.Range(0, 80).Select(_ => Rng.NextDouble() * 20).Order()];
    private static readonly double[] Y = [.. T.Select(t => Math.Cos(2 * Math.PI * 0.4 * t + 0.3) + 0.3 * (Rng.NextDouble() - 0.5))];
    private static readonly double[] F = [.. Enumerable.Range(0, 60).Select(i => 0.05 + i * 1.45 / 59)];

    [Fact]
    public void PeakAtTheTone()
    {
        double[] p = Spectral.LombScargle(T, Y, F);
        int k = Array.IndexOf(p, p.Max());
        Assert.True(Math.Abs(F[k] - 0.4) < F[1] - F[0]);
        Assert.All(p, v => Assert.InRange(v, 0, 1 + 1e-12));
    }

    [Fact]
    public void StandardIgnoresScaleAndPowerScalesByItsSquare()
    {
        double[] y7 = [.. Y.Select(v => 7 * v)];
        double[] a = Spectral.LombScargle(T, Y, F), b = Spectral.LombScargle(T, y7, F);
        double[] pa = Spectral.LombScargle(T, Y, F, normalization: LombScargleNormalization.Power);
        double[] pb = Spectral.LombScargle(T, y7, F, normalization: LombScargleNormalization.Power);
        for (int i = 0; i < F.Length; i++)
        {
            Assert.Equal(a[i], b[i], 1e-12);
            Assert.Equal(49 * pa[i], pb[i], 1e-9);
        }
    }

    [Fact]
    public void CenterRemovesTheMean()
    {
        double[] shifted = [.. Y.Select(v => v + 5)];
        double[] a = Spectral.LombScargle(T, Y, F), b = Spectral.LombScargle(T, shifted, F);
        for (int i = 0; i < F.Length; i++)
            Assert.Equal(a[i], b[i], 1e-9);
        // without centering, a large mean shows at the lowest frequencies
        var power = LombScargleNormalization.Power;
        Assert.True(Spectral.LombScargle(T, shifted, F, false, power)[0] > 10 * Spectral.LombScargle(T, Y, F, normalization: power)[0]);
    }

    [Fact]
    public void EmptyFrequencies() => Assert.Empty(Spectral.LombScargle(T, Y, []));

    [Fact]
    public void RejectsUnknownNormalization() =>
        Assert.ThrowsAny<ArgumentException>(() => Spectral.LombScargle(T, Y, F, normalization: (LombScargleNormalization)7));

    [Theory]
    [InlineData(1, 1, 0.1)]
    [InlineData(3, 2, 0.1)]
    [InlineData(3, 3, 0.0)]
    [InlineData(3, 3, double.NaN)]
    public void RejectsBadShapes(int nt, int ny, double f) =>
        Assert.ThrowsAny<ArgumentException>(() => Spectral.LombScargle(new double[nt], [.. Enumerable.Range(0, ny).Select(i => (double)i)], [f]));
}
