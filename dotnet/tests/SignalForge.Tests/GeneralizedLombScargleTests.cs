using Xunit;

namespace SignalForge.Tests;

/// <summary>Generalized Lomb-Scargle (conventions: Spectra, Generalized Lomb-Scargle; ADR 0081).</summary>
public sealed class GeneralizedLombScargleTests
{
    private static (double[] T, double[] Y, double[] Sigma) Uneven(int seed, int n = 60)
    {
        var rng = new Random(seed);
        double[] t = [.. Enumerable.Range(0, n).Select(_ => 30 * rng.NextDouble()).Order()];
        double[] y = [.. t.Select(v => 4 + Math.Sin(2 * Math.PI * 0.23 * v) + (0.5 * (rng.NextDouble() - 0.5)))];
        double[] sigma = [.. t.Select(_ => 0.3 + (1.2 * rng.NextDouble()))];
        return (t, y, sigma);
    }

    private static double Det(double[,] m) =>
        (m[0, 0] * ((m[1, 1] * m[2, 2]) - (m[1, 2] * m[2, 1])))
        - (m[0, 1] * ((m[1, 0] * m[2, 2]) - (m[1, 2] * m[2, 0])))
        + (m[0, 2] * ((m[1, 0] * m[2, 1]) - (m[1, 1] * m[2, 0])));

    [Fact]
    public void MatchesAWeightedLeastSquaresFit()
    {
        var (t, y, sigma) = Uneven(1);
        double[] f = [0.07, 0.23, 0.41, 0.9];
        double[] got = Spectral.GeneralizedLombScargle(t, y, f, sigma);
        double[] w = [.. sigma.Select(s => 1 / (s * s))];
        double mean = w.Zip(y, (a, b) => a * b).Sum() / w.Sum();
        double chi0 = w.Zip(y, (a, b) => a * (b - mean) * (b - mean)).Sum();
        for (int k = 0; k < f.Length; k++)
        {
            // the 3×3 weighted normal equations by Cramer's rule
            double om = 2 * Math.PI * f[k];
            double[][] basis = [[.. t.Select(v => Math.Cos(om * v))], [.. t.Select(v => Math.Sin(om * v))], [.. t.Select(_ => 1.0)]];
            var g = new double[3, 3];
            var r = new double[3];
            for (int i = 0; i < 3; i++)
            {
                for (int n = 0; n < t.Length; n++)
                {
                    r[i] += w[n] * basis[i][n] * y[n];
                    for (int j = 0; j < 3; j++)
                        g[i, j] += w[n] * basis[i][n] * basis[j][n];
                }
            }
            double d = Det(g);
            var coef = new double[3];
            for (int c = 0; c < 3; c++)
            {
                var m = (double[,])g.Clone();
                for (int i = 0; i < 3; i++)
                    m[i, c] = r[i];
                coef[c] = Det(m) / d;
            }
            double chi = 0;
            for (int n = 0; n < t.Length; n++)
            {
                double e = y[n] - ((coef[0] * basis[0][n]) + (coef[1] * basis[1][n]) + coef[2]);
                chi += w[n] * e * e;
            }
            Assert.Equal((chi0 - chi) / chi0, got[k], 1e-9);
        }
    }

    [Fact]
    public void EqualsTheClassicFormOnEvenSamplesAtBins()
    {
        double[] n = [.. Enumerable.Range(0, 32).Select(i => (double)i)];
        double[] x = [.. n.Select(v => (1.5 * Math.Cos((2 * Math.PI * 3 / 32 * v) + 0.4)) + (0.3 * Math.Sin(2 * Math.PI * 5 / 32 * v)) + 2)];
        double[] f = [3 / 32.0, 5 / 32.0, 7 / 32.0, 11 / 32.0];
        foreach (var norm in new[] { LombScargleNormalization.Standard, LombScargleNormalization.Power })
        {
            double[] g = Spectral.GeneralizedLombScargle(n, x, f, normalization: norm);
            double[] c = Spectral.LombScargle(n, x, f, normalization: norm);
            for (int i = 0; i < f.Length; i++)
                Assert.Equal(c[i], g[i], 1e-12);
        }
    }

    [Fact]
    public void FloatingMeanKeepsThePowerTheClassicFormLoses()
    {
        // sampled mostly near the peaks: measured classic 0.960, generalized 1 (an exact fit)
        double[] t = [.. Enumerable.Range(0, 12).SelectMany(k => new[] { k - 0.05, k, k + 0.05 }), 5.5, 8.5];
        double[] y = [.. t.Select(v => 2 + Math.Cos(2 * Math.PI * 0.9 * v))];
        Assert.Equal(1.0, Spectral.GeneralizedLombScargle(t, y, [0.9])[0], 1e-12);
        Assert.True(Spectral.LombScargle(t, y, [0.9])[0] < 0.97);
    }

    [Fact]
    public void ScaleAndShift()
    {
        var (t, y, sigma) = Uneven(2);
        double[] f = [0.1, 0.23, 0.5];
        double[] three = [.. sigma.Select(s => 3 * s)];
        double[] baseP = Spectral.GeneralizedLombScargle(t, y, f, sigma);
        double[] power = Spectral.GeneralizedLombScargle(t, y, f, sigma, LombScargleNormalization.Power);
        double[] scaled = Spectral.GeneralizedLombScargle(t, y, f, three);
        double[] scaledPower = Spectral.GeneralizedLombScargle(t, y, f, three, LombScargleNormalization.Power);
        double[] moved = Spectral.GeneralizedLombScargle([.. t.Select(v => v + 123.4)], [.. y.Select(v => (5 * v) - 7)], f, sigma);
        double[] unit = Spectral.GeneralizedLombScargle(t, y, f);
        double[] ones = Spectral.GeneralizedLombScargle(t, y, f, [.. t.Select(_ => 1.0)]);
        for (int i = 0; i < f.Length; i++)
        {
            Assert.Equal(baseP[i], scaled[i], 1e-12);
            Assert.True(Math.Abs(scaledPower[i] - (power[i] / 9)) <= 1e-12 * power[i]);
            Assert.True(Math.Abs(moved[i] - baseP[i]) <= 1e-9 * baseP[i]);
            Assert.Equal(unit[i], ones[i], 1e-15);
        }
    }

    [Fact]
    public void Rejects()
    {
        double[] t = [0.0, 1.0, 2.0], y = [1.0, 2.0, 0.5];
        Assert.ThrowsAny<ArgumentException>(() => Spectral.GeneralizedLombScargle(t, y.AsSpan()[..2], [0.3]));
        Assert.ThrowsAny<ArgumentException>(() => Spectral.GeneralizedLombScargle(t, y, [0.3], [1.0, 0.0, 1.0]));
        Assert.ThrowsAny<ArgumentException>(() => Spectral.GeneralizedLombScargle(t, y, [0.3], [1.0, 1.0]));
        Assert.ThrowsAny<ArgumentException>(() => Spectral.GeneralizedLombScargle(t, y, [-0.3]));
        Assert.ThrowsAny<ArgumentException>(() => Spectral.GeneralizedLombScargle(t, y, [0.3], normalization: (LombScargleNormalization)(-1)));
        Assert.ThrowsAny<ArgumentException>(() => Spectral.GeneralizedLombScargle(t, [2.0, 2.0, 2.0], [0.3]));
    }
}
