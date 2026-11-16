using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Sample clock drift against a tone, the fixed offset and its limits (conventions:
/// Channel, Sample clock drift; ADR 0102).</summary>
public class ClockDriftTests
{
    // t[n+1] = r + (1 + d) t[n] summed with compensation, an independent route to the positions.
    private static List<double> Positions(int n, double p0, double p1)
    {
        double r = 1 + p0 / 1e6, d = (p1 - p0) / 1e6 / (n - 1);
        var t = new List<double>();
        double s = 0, c = 0;
        while (s <= n - 1)
        {
            t.Add(s);
            double step = r + d * s - c, next = s + step;
            c = next - s - step;
            s = next;
        }
        return t;
    }

    [Theory]
    [InlineData(-1e5, 1e5)]
    [InlineData(3e4, -2e4)]
    [InlineData(0.0, 400.0)]
    [InlineData(5e4, 5.1e4)]
    public void ToneIsReadAtTheDriftingPositions(double p0, double p1)
    {
        Complex[] x = [.. Enumerable.Range(0, 300).Select(n => Complex.FromPolarCoordinates(1, 2 * Math.PI * 0.05 * n))];
        Complex[] y = Channel.ClockDrift(x, p0, p1);
        List<double> t = Positions(300, p0, p1);
        Assert.Equal(t.Count, y.Length);
        for (int n = 0; n < y.Length; n++)
            if (t[n] > 16 && t[n] < 299 - 16) // the default kernel's error floor is about 2e-5 here
                Assert.True(Complex.Abs(y[n] - Complex.FromPolarCoordinates(1, 2 * Math.PI * 0.05 * t[n])) < 5e-5, $"n {n}");
    }

    [Fact]
    public void EqualOffsetsAreTheFixedOffset()
    {
        var rng = new Random(5);
        Complex[] x = [.. Enumerable.Range(0, 200).Select(_ => new Complex(rng.NextDouble() - 0.5, rng.NextDouble() - 0.5))];
        foreach (double ppm in new[] { -1e5, -20.0, 0.0, 7e3 })
        {
            Assert.Equal(Channel.ClockOffset(x, ppm), Channel.ClockDrift(x, ppm, ppm));
            Assert.Equal(Channel.ClockOffset(x, ppm, 3), Channel.ClockDrift(x, ppm, ppm, 3));
        }
    }

    [Fact]
    public void LengthByHand() => // d = 0.01: t_n = (1.01^n − 1)/0.01 ≤ 10 needs n ≤ 9.58
        Assert.Equal(10, Channel.ClockDrift(Enumerable.Repeat(Complex.One, 11).ToArray(), 0, 1e5).Length);

    [Fact]
    public void SmallInputs()
    {
        Assert.Empty(Channel.ClockDrift([], 10, -10));
        Assert.Equal([new Complex(2, -1)], Channel.ClockDrift([new Complex(2, -1)], 7e4, -3e4));
        Assert.Single(Channel.ClockDrift([1, 2], 1e5, 1e5));
        Assert.Equal(2, Channel.ClockDrift([1, 2], -1e5, -1e5).Length);
    }

    [Theory]
    [InlineData(1.000001e5, 20.0, 16)]
    [InlineData(10.0, -2e5, 16)]
    [InlineData(double.NaN, 20.0, 16)]
    [InlineData(10.0, double.PositiveInfinity, 16)]
    [InlineData(10.0, 20.0, 0)]
    public void BadArguments(double p0, double p1, int halfWidth) =>
        Assert.Throws<ArgumentOutOfRangeException>(() => Channel.ClockDrift([1, 1, 1, 1], p0, p1, halfWidth));
}
