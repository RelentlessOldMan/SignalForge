using Xunit;

namespace SignalForge.Tests;

/// <summary>Lomb-Scargle false-alarm probability and frequency grid (conventions: Spectra; ADR 0062).</summary>
public sealed class LombScargleFapTests
{
    private static readonly Random Rng = new(62);

    private static readonly int[] Counts = [1, 10, 100, 1_000_000];

    private static readonly double[] Levels = [0.1, 0.25, 0.4];

    private static double Gauss() => Math.Sqrt(-2 * Math.Log(1 - Rng.NextDouble())) * Math.Cos(2 * Math.PI * Rng.NextDouble());

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void SingleFrequencySurvivalMatchesNoise(bool center)
    {
        // Centered needs even times at a bin for the Beta form to be exact; uncentered holds for any.
        const int n = 24, trials = 4000;
        double[] t = center
            ? [.. Enumerable.Range(0, n).Select(i => (double)i)]
            : [.. Enumerable.Range(0, n).Select(_ => 30 * Rng.NextDouble()).Order()];
        double[] f = [5.0 / n];
        var z = new double[trials];
        for (int i = 0; i < trials; i++)
            z[i] = Spectral.LombScargle(t, [.. Enumerable.Range(0, n).Select(_ => Gauss())], f, center)[0];
        foreach (double level in Levels)
        {
            double p = Spectral.LombScargleFalseAlarm(level, n, center: center);
            double se = Math.Sqrt(p * (1 - p) / trials);
            Assert.True(Math.Abs(z.Count(v => v > level) / (double)trials - p) < 4 * se, $"level {level}");
        }
    }

    [Fact]
    public void ManyFrequenciesIsMonotoneAndBounded()
    {
        double[] p = [.. Counts.Select(m => Spectral.LombScargleFalseAlarm(0.3, 50, m))];
        Assert.Equal(p.Order(), p);
        Assert.True(p[0] > 0 && p[^1] <= 1);
    }

    [Fact]
    public void TinySingleProbabilityKeepsPrecision()
    {
        double expected = 1000 * Math.Pow(0.5, 80);
        Assert.Equal(1, Spectral.LombScargleFalseAlarm(0.75, 83, 1000) / expected, 1e-12);
    }

    [Fact]
    public void GridFeedsThePeriodogram()
    {
        double[] t = [.. Enumerable.Range(0, 60).Select(_ => 40 * Rng.NextDouble()).Order()];
        double[] f = Spectral.LombScargleFrequencies(t);
        double span = t[^1] - t[0];
        Assert.Equal(1 / (5 * span), f[0], 1e-15);
        Assert.Equal(150, f.Length);
        double[] y = [.. t.Select(v => Math.Sin(2 * Math.PI * f[40] * v))];
        var p = Spectral.LombScargle(t, y, f);
        Assert.Equal(40, Array.IndexOf(p, p.Max()));
    }

    [Theory]
    [InlineData(1.01, 10, 1, true)]
    [InlineData(double.NaN, 10, 1, true)]
    [InlineData(-0.1, 10, 1, true)]
    [InlineData(0.5, 3, 1, true)]
    [InlineData(0.5, 2, 1, false)]
    [InlineData(0.5, 10, 0, true)]
    public void FalseAlarmRejects(double power, int n, int m, bool center) =>
        Assert.ThrowsAny<ArgumentException>(() => Spectral.LombScargleFalseAlarm(power, n, m, center));

    public static TheoryData<double[], double, double?> BadGrids() => new()
    {
        { [1.0], 5, null },
        { [2.0, 2.0], 5, null },
        { [0.0, double.NaN], 5, null },
        { [0.0, 1.0], 0, null },
        { [0.0, 1.0], double.PositiveInfinity, null },
        { [0.0, 1.0], 5, 0.0 },
        { [0.0, 1.0], 1e300, 1e300 },
    };

    [Theory]
    [MemberData(nameof(BadGrids))]
    public void FrequenciesRejects(double[] times, double oversampling, double? maxFrequency) =>
        Assert.ThrowsAny<ArgumentException>(() => Spectral.LombScargleFrequencies(times, oversampling, maxFrequency));
}
