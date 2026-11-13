using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Block fading: the gain's statistics against Rician theory, one gain per block
/// (conventions: Channel, Block fading).</summary>
public class FadingTests
{
    private const int N = 200_000;

    private static Complex[] Ones(int n) => [.. Enumerable.Repeat(Complex.One, n)];

    [Theory]
    [InlineData(0.0)]
    [InlineData(1.0)]
    [InlineData(3.0)]
    [InlineData(10.0)]
    public void GainStatistics(double k)
    {
        Complex[] g = Channel.RicianFading(Ones(N), k, 1, seed: 4);
        double re = g.Average(z => z.Real), im = g.Average(z => z.Imaginary);
        Assert.Equal(1, g.Average(z => z.Real * z.Real + z.Imaginary * z.Imaginary), 0.015);
        Assert.Equal(Math.Sqrt(k / (k + 1)), re, 0.01);
        Assert.Equal(0, im, 0.01);
        Assert.Equal(1, g.Average(z => (z.Real - re) * (z.Real - re)) / (0.5 / (k + 1)), 0.02);
        Assert.Equal(1, g.Average(z => (z.Imaginary - im) * (z.Imaginary - im)) / (0.5 / (k + 1)), 0.02);
    }

    [Fact]
    public void RayleighPowerIsExponential()
    {
        double[] p = [.. Channel.RicianFading(Ones(N), 0, 1, seed: 8).Select(z => z.Real * z.Real + z.Imaginary * z.Imaginary)];
        foreach (double x in new[] { 0.1, 0.5, 1.0, 2.0, 4.0 })
            Assert.Equal(1 - Math.Exp(-x), p.Count(v => v < x) / (double)N, 0.005);
    }

    [Fact]
    public void OneGainPerBlock()
    {
        Complex[] x = [.. Enumerable.Range(1, 11).Select(n => n * new Complex(1, -0.5))];
        Complex[] y = Channel.RicianFading(x, 2, 4, seed: 1);
        Complex[] g = [.. y.Select((v, i) => v / x[i])];
        for (int n = 0; n < 11; n++)
            Assert.True(Complex.Abs(g[n] - g[n / 4 * 4]) <= 1e-15 * Complex.Abs(g[n / 4 * 4]));
        Assert.Equal(3, new[] { g[0], g[4], g[8] }.Distinct().Count());
    }

    [Fact]
    public void SeedReproducibleAndInfiniteKIsIdentity()
    {
        Assert.Equal(Channel.RicianFading(Ones(50), 1, 5, seed: 9), Channel.RicianFading(Ones(50), 1, 5, new Random(9)));
        Complex[] x = [new(1, 2), -3, new(0, 0.5)];
        Assert.Equal(x, Channel.RicianFading(x, double.PositiveInfinity, 1, seed: 0));
    }

    [Fact]
    public void BadArgumentsThrow()
    {
        Assert.ThrowsAny<ArgumentException>(() => Channel.RicianFading([Complex.One], -1, 1, seed: 0));
        Assert.ThrowsAny<ArgumentException>(() => Channel.RicianFading([Complex.One], double.NaN, 1, seed: 0));
        Assert.ThrowsAny<ArgumentException>(() => Channel.RicianFading([Complex.One], 1, 0, seed: 0));
        Assert.Throws<ArgumentNullException>(() => Channel.RicianFading([Complex.One], 1, 1, (Random)null!));
    }
}
