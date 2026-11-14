using Xunit;

namespace SignalForge.Tests;

/// <summary>Lomb-Scargle false-alarm level (conventions: Spectra, Lomb-Scargle false-alarm level; ADR 0082).</summary>
public sealed class LombScargleFalseAlarmLevelTests
{
    [Fact]
    public void InvertsTheFalseAlarmProbability()
    {
        foreach (var (n, m, center) in new[] { (10, 1, true), (57, 30, true), (500, 4000, false), (4, 1, false) })
        {
            foreach (double p in new[] { 1e-12, 1e-6, 0.01, 0.5, 0.99 })
            {
                double z = Spectral.LombScargleFalseAlarmLevel(p, n, m, center);
                double back = Spectral.LombScargleFalseAlarm(z, n, m, center);
                // near z = 1 the forward function's 1 − z keeps only the digits left after rounding z
                double tol = z < 1 - 1e-6 ? 1e-9 : 1e-3;
                Assert.True(Math.Abs(back - p) <= tol * p, $"N={n} M={m} p={p}: {back}");
            }
        }
    }

    [Fact]
    public void FallsAsTheProbabilityRises()
    {
        double[] levels = [.. new[] { 0, 0.01, 0.1, 1 }.Select(p => Spectral.LombScargleFalseAlarmLevel(p, 40, 50))];
        Assert.Equal(1.0, levels[0]);
        Assert.Equal(0.0, levels[^1]);
        for (int i = 1; i < levels.Length; i++)
            Assert.True(levels[i - 1] > levels[i]);
    }

    [Fact]
    public void WhiteNoiseExceedsItAtTheStatedRate()
    {
        // at one frequency the generalized value of Gaussian noise with the stated sigma is
        // Beta(1, (N - 3)/2) exactly
        var rng = new Random(82);
        double Gauss() => Math.Sqrt(-2 * Math.Log(1 - rng.NextDouble())) * Math.Cos(2 * Math.PI * rng.NextDouble());
        const int n = 20, trials = 4000;
        const double p = 0.1;
        double z = Spectral.LombScargleFalseAlarmLevel(p, n);
        int hits = 0;
        for (int k = 0; k < trials; k++)
        {
            double[] t = [.. Enumerable.Range(0, n).Select(_ => 10 * rng.NextDouble()).Order()];
            double[] sigma = [.. t.Select(_ => 0.5 + (1.5 * rng.NextDouble()))];
            double[] y = [.. sigma.Select(s => 3 + (s * Gauss()))];
            if (Spectral.GeneralizedLombScargle(t, y, [0.37], sigma)[0] > z)
                hits++;
        }
        Assert.True(Math.Abs(((double)hits / trials) - p) < 4 * Math.Sqrt(p * (1 - p) / trials), $"{hits} of {trials}");
    }

    [Fact]
    public void Rejects()
    {
        foreach (double p in new[] { -0.1, 1.5, double.NaN })
            Assert.ThrowsAny<ArgumentException>(() => Spectral.LombScargleFalseAlarmLevel(p, 10));
        Assert.ThrowsAny<ArgumentException>(() => Spectral.LombScargleFalseAlarmLevel(0.5, 3));
        Assert.ThrowsAny<ArgumentException>(() => Spectral.LombScargleFalseAlarmLevel(0.5, 2, center: false));
        Assert.ThrowsAny<ArgumentException>(() => Spectral.LombScargleFalseAlarmLevel(0.5, 10, 0));
    }
}
