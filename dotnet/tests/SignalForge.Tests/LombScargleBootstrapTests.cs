using Xunit;

namespace SignalForge.Tests;

/// <summary>Bootstrap maxima for a Lomb-Scargle search (conventions: Spectra; ADR 0101).</summary>
public sealed class LombScargleBootstrapTests
{
    private static readonly Random Rng = new(101);
    private static readonly double[] Levels = [0.2, 0.25];

    private static double Gauss() => Math.Sqrt(-2 * Math.Log(1 - Rng.NextDouble())) * Math.Cos(2 * Math.PI * Rng.NextDouble());

    private static double[] Uneven(int n, double span) => [.. Enumerable.Range(0, n).Select(_ => span * Rng.NextDouble()).Order()];

    [Fact]
    public void NoiseAgreesWithBaluev()
    {
        // Baluev's estimate is close for small probabilities and errs high, never far low.
        double[] t = Uneven(60, 30);
        double[] y = [.. Enumerable.Range(0, 60).Select(_ => Gauss())];
        double[] f = Spectral.LombScargleFrequencies(t, 5, 1);
        const int draws = 300;
        double[] peaks = Spectral.LombScargleBootstrap(t, y, f, draws, 5);
        foreach (double level in Levels)
        {
            double p = Spectral.LombScargleFalseAlarmBaluev(level, t, 1);
            double se = Math.Sqrt(p * (1 - p) / draws);
            double seen = peaks.Count(v => v > level) / (double)draws;
            Assert.True(seen > 0.5 * p - 4 * se && seen < p + 4 * se, $"level {level}: {seen} vs {p}");
        }
    }

    [Fact]
    public void AStrongToneIsAboveEveryDraw()
    {
        double[] t = Uneven(50, 30);
        double[] y = [.. t.Select(x => Math.Sin(2 * Math.PI * 0.37 * x) + 0.3 * Gauss())];
        double[] f = Spectral.LombScargleFrequencies(t, 5, 1);
        double observed = Spectral.LombScargle(t, y, f).Max();
        Assert.All(Spectral.LombScargleBootstrap(t, y, f, 100, 1), v => Assert.True(v < observed));
    }

    [Fact]
    public void ShapeSeedAndBounds()
    {
        double[] t = [.. Enumerable.Range(0, 20).Select(i => (double)i)];
        double[] y = [.. t.Select(_ => Gauss())];
        double[] f = [0.1, 0.2, 0.3];
        double[] a = Spectral.LombScargleBootstrap(t, y, f, 25, 3);
        Assert.Equal(25, a.Length);
        Assert.All(a, v => Assert.InRange(v, 0, 1));
        Assert.Equal(a, Spectral.LombScargleBootstrap(t, y, f, 25, 3));
        Assert.Equal(a, Spectral.LombScargleBootstrap(t, y, f, 25, new Random(3)));
    }

    [Theory]
    [InlineData(new double[] { 1, 1, 1, 2 }, true)]
    [InlineData(new double[] { 0, 0, 0, 1 }, false)]
    public void DrawsThatCannotBeNormalizedGiveZero(double[] values, bool center)
    {
        double[] peaks = Spectral.LombScargleBootstrap([0, 1.3, 2.1, 3.7], values, [0.2, 0.4], 200, 2, center);
        Assert.Contains(0.0, peaks);
        Assert.Contains(peaks, v => v > 0);
    }

    [Fact]
    public void AConstantSeriesUncenteredRepeatsItsPeak()
    {
        double[] t = [0, 0.7, 1.9, 3.2], f = [0.13, 0.31], y = [2, 2, 2, 2];
        double peak = Spectral.LombScargle(t, y, f, center: false).Max();
        Assert.Equal([peak, peak, peak, peak], Spectral.LombScargleBootstrap(t, y, f, 4, 9, center: false));
    }

    [Theory]
    [InlineData(new double[] { 1, 2, 3, 5 }, new double[] { 0.2 }, 0)]
    [InlineData(new double[] { 1, 2, 3, 5 }, new double[] { 0.2 }, -1)]
    [InlineData(new double[] { 1, 2, 3, 5 }, new double[0], 3)]
    [InlineData(new double[] { 2, 2, 2, 2 }, new double[] { 0.2 }, 3)]
    [InlineData(new double[] { 1, 2, 3 }, new double[] { 0.2 }, 3)]
    [InlineData(new double[] { 1, 2, double.NaN, 5 }, new double[] { 0.2 }, 3)]
    public void Rejects(double[] values, double[] frequencies, int draws) =>
        Assert.ThrowsAny<ArgumentException>(() => Spectral.LombScargleBootstrap([0, 1, 2, 3], values, frequencies, draws, 1));

    [Fact]
    public void RejectsANullGenerator() =>
        Assert.Throws<ArgumentNullException>(() => Spectral.LombScargleBootstrap([0, 1, 2, 3], [1, 2, 3, 5], [0.2], 3, null!));
}
