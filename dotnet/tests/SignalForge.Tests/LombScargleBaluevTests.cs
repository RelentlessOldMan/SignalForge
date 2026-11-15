using Xunit;

namespace SignalForge.Tests;

/// <summary>Baluev false-alarm probability for a Lomb-Scargle search (conventions: Spectra; ADR 0098).</summary>
public sealed class LombScargleBaluevTests
{
    private static readonly Random Rng = new(98);

    private static double Gauss() => Math.Sqrt(-2 * Math.Log(1 - Rng.NextDouble())) * Math.Cos(2 * Math.PI * Rng.NextDouble());

    private static double[] Uneven(int n, double span) => [.. Enumerable.Range(0, n).Select(_ => span * Rng.NextDouble()).Order()];

    [Fact]
    public void SearchOverAGridIsCloseToNoise()
    {
        // Baluev's estimate is close for small probabilities and errs high, never far low.
        const int n = 40, trials = 600;
        double[] t = Uneven(n, 40);
        double[] f = Spectral.LombScargleFrequencies(t, 5, 0.5);
        var peaks = new double[trials];
        for (int i = 0; i < trials; i++)
            peaks[i] = Spectral.LombScargle(t, [.. Enumerable.Range(0, n).Select(_ => Gauss())], f).Max();
        foreach (double level in new[] { 0.3, 0.35, 0.4 })
        {
            double p = Spectral.LombScargleFalseAlarmBaluev(level, t, 0.5);
            double se = Math.Sqrt(p * (1 - p) / trials);
            double seen = peaks.Count(v => v > level) / (double)trials;
            Assert.True(seen > 0.5 * p - 4 * se && seen < p + 4 * se, $"level {level}: {seen} vs {p}");
        }
    }

    [Fact]
    public void HandCaseAtFourSamples()
    {
        // N_H = 3: gamma = sqrt(2/3)·sqrt(pi)/2, and (1 − z)^((N_K − 1)/2) = 1.
        double tau = Math.Sqrt(4 * Math.PI * 1.25) * Math.Sqrt(2 / 3.0) * (Math.Sqrt(Math.PI) / 2) * Math.Sqrt(0.75);
        double expected = 1 - (1 - Math.Sqrt(0.5)) * Math.Exp(-tau);
        Assert.Equal(expected, Spectral.LombScargleFalseAlarmBaluev(0.5, [0, 1, 2, 3], 1), 1e-14);
    }

    [Fact]
    public void IsMonotoneAndBounded()
    {
        double[] t = Uneven(30, 10);
        double[] p = [.. Enumerable.Range(0, 21).Select(i => Spectral.LombScargleFalseAlarmBaluev(i / 20.0, t, 2))];
        Assert.Equal(p.OrderDescending(), p);
        Assert.Equal((1.0, 0.0), (p[0], p[^1]));
        double[] q = [.. new[] { 0.1, 1, 10 }.Select(f => Spectral.LombScargleFalseAlarmBaluev(0.3, t, f))];
        Assert.Equal(q.Order(), q);
        Assert.All(q, x => Assert.InRange(x, 0, 1));
    }

    [Fact]
    public void AtLeastTheOneFrequencyChance()
    {
        double[] t = [.. Enumerable.Range(0, 20).Select(i => (double)i)];
        foreach (double z in new[] { 0.1, 0.4, 0.7 })
            Assert.True(Spectral.LombScargleFalseAlarmBaluev(z, t, 0.5) >= Spectral.LombScargleFalseAlarm(z, 20));
    }

    [Fact]
    public void ShiftingTheTimesChangesNothing()
    {
        double[] t = Uneven(25, 10);
        double a = Spectral.LombScargleFalseAlarmBaluev(0.4, t, 1.5);
        double b = Spectral.LombScargleFalseAlarmBaluev(0.4, [.. t.Select(x => x + 1e3)], 1.5);
        Assert.Equal(a, b, a * 1e-9);
    }

    [Theory]
    [InlineData(-0.1, new double[] { 0, 1, 2, 3 }, 1.0, true)]
    [InlineData(1.01, new double[] { 0, 1, 2, 3 }, 1.0, true)]
    [InlineData(double.NaN, new double[] { 0, 1, 2, 3 }, 1.0, true)]
    [InlineData(0.5, new double[] { 0, 1, 2 }, 1.0, true)]
    [InlineData(0.5, new double[] { 0, 1 }, 1.0, false)]
    [InlineData(0.5, new double[] { 1, 1, 1, 1 }, 1.0, true)]
    [InlineData(0.5, new double[] { 0, 1, 2, double.NaN }, 1.0, true)]
    [InlineData(0.5, new double[] { 0, 1, 2, 3 }, 0.0, true)]
    [InlineData(0.5, new double[] { 0, 1, 2, 3 }, -1.0, true)]
    [InlineData(0.5, new double[] { 0, 1, 2, 3 }, double.PositiveInfinity, true)]
    public void Rejects(double power, double[] times, double maxFrequency, bool center) =>
        Assert.ThrowsAny<ArgumentException>(() => Spectral.LombScargleFalseAlarmBaluev(power, times, maxFrequency, center));
}
