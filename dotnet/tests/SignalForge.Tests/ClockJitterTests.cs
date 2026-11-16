using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Sample clock jitter against the jitter SNR of a tone (conventions: Channel, Sample
/// clock jitter; ADR 0104).</summary>
public class ClockJitterTests
{
    private static Complex[] Tone(int n, double f) =>
        [.. Enumerable.Range(0, n).Select(k => Complex.FromPolarCoordinates(1, 2 * Math.PI * f * k))];

    [Theory]
    [InlineData(0.05, 0.01)]
    [InlineData(0.05, 0.2)]
    [InlineData(0.2, 0.05)]
    [InlineData(0.2, 0.3)]
    public void ToneErrorPowerIsTheJitterFormula(double f, double rms)
    {
        const int n = 20000;
        Complex[] x = Tone(n, f);
        Complex[] y = Channel.ClockJitter(x, rms, 11);
        double sum = 0;
        for (int k = 16; k < n - 16; k++)
            sum += Math.Pow(Complex.Abs(y[k] - x[k]), 2);
        double got = sum / (n - 32);
        // E|e^{jag} − 1|² = 2(1 − e^{−a²/2}), a = 2πf·rms: the Gaussian characteristic function
        double a = 2 * Math.PI * f * rms;
        double want = 2 * (1 - Math.Exp(-a * a / 2));
        Assert.True(Math.Abs(got - want) < 0.05 * want, $"{got} vs {want}");
    }

    [Fact]
    public void TheOffsetsAreWhiteWithTheGivenSpread()
    {
        const int n = 20000;
        const double f = 0.01, rms = 0.1;
        Complex[] x = Tone(n, f);
        Complex[] y = Channel.ClockJitter(x, rms, 4);
        double[] d = [.. Enumerable.Range(16, n - 32).Select(k => (y[k] / x[k]).Phase / (2 * Math.PI * f))];
        double mean = d.Average();
        double sd = Math.Sqrt(d.Select(v => (v - mean) * (v - mean)).Average());
        double lag = Enumerable.Range(0, d.Length - 1).Select(k => (d[k] - mean) * (d[k + 1] - mean)).Average() / (sd * sd);
        Assert.True(Math.Abs(mean) < 4 * rms / Math.Sqrt(d.Length));
        Assert.True(Math.Abs(sd - rms) < 0.03 * rms, $"sd {sd}");
        Assert.True(Math.Abs(lag) < 0.03, $"lag {lag}");
    }

    [Fact]
    public void ZeroRmsReturnsTheInputAndSeedsRepeat()
    {
        Complex[] x = [new(1, 2), new(0, -0.5), 3, new(0.25, -1)];
        Assert.Equal(x, Channel.ClockJitter(x, 0, 1));
        Complex[] y = Tone(50, 0.05);
        Assert.Equal(Channel.ClockJitter(y, 0.2, 9), Channel.ClockJitter(y, 0.2, new Random(9)));
        Assert.NotEqual(Channel.ClockJitter(y, 0.2, 10), Channel.ClockJitter(y, 0.2, 9));
        Assert.Empty(Channel.ClockJitter([], 0.4, 1));
        Assert.Equal(50, Channel.ClockJitter(y, 0.5, 2, 4).Length);
    }

    [Theory]
    [InlineData(-0.01, 16)]
    [InlineData(0.51, 16)]
    [InlineData(double.NaN, 16)]
    [InlineData(double.PositiveInfinity, 16)]
    [InlineData(0.1, 0)]
    public void BadArguments(double rms, int halfWidth)
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => Channel.ClockJitter([1, 1, 1, 1], rms, 1, halfWidth));
        Assert.Throws<ArgumentNullException>(() => Channel.ClockJitter([1, 1], 0.1, (Random)null!));
    }
}
