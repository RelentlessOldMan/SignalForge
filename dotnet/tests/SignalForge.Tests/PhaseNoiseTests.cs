using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Phase noise: the Wiener walk's statistics against theory (conventions: Channel, Phase
/// noise). Seeded, so each check is deterministic; tolerances are several standard errors wide.</summary>
public class PhaseNoiseTests
{
    private static Complex[] Ones(int n) => [.. Enumerable.Repeat(Complex.One, n)];

    private static double[] Phase(Complex[] y)
    {
        var phi = new double[y.Length];
        for (int i = 1; i < y.Length; i++)
            phi[i] = phi[i - 1] + (y[i] * Complex.Conjugate(y[i - 1])).Phase;
        return phi;
    }

    private static double Variance(IEnumerable<double> v)
    {
        double[] a = [.. v];
        double mean = a.Average();
        return a.Sum(x => (x - mean) * (x - mean)) / a.Length;
    }

    [Fact]
    public void IncrementsHaveTheLinewidthsVariance()
    {
        const double fs = 1e6, linewidth = 2000;
        const int n = 200_000, lag = 25;
        double sigma2 = 2 * Math.PI * linewidth / fs;
        double[] phi = Phase(Channel.PhaseNoise(Ones(n), linewidth, fs, 1));
        double[] steps = [.. Enumerable.Range(1, n - 1).Select(i => phi[i] - phi[i - 1])];
        Assert.True(Math.Abs(steps.Average()) < 5 * Math.Sqrt(sigma2 / n));
        Assert.True(Math.Abs(Variance(steps) / sigma2 - 1) < 5 * Math.Sqrt(2.0 / n), $"{Variance(steps)}");
        double lagged = Variance(Enumerable.Range(lag, n - lag).Select(i => phi[i] - phi[i - lag]));
        Assert.True(Math.Abs(lagged / (lag * sigma2) - 1) < 0.05, $"{lagged}");
    }

    [Fact]
    public void TheMeanPhasorDecaysAsTheorySays()
    {
        const double fs = 1000, linewidth = 10;
        const int n = 40, runs = 4000;
        var rng = new Random(2);
        var total = new Complex[n];
        for (int r = 0; r < runs; r++)
        {
            Complex[] y = Channel.PhaseNoise(Ones(n), linewidth, fs, rng);
            for (int i = 0; i < n; i++)
                total[i] += y[i];
        }
        double sigma2 = 2 * Math.PI * linewidth / fs, tol = 5 / Math.Sqrt(2.0 * runs);
        for (int i = 0; i < n; i++)
        {
            Assert.Equal(Math.Exp(-i * sigma2 / 2), total[i].Real / runs, tol);
            Assert.Equal(0, total[i].Imaginary / runs, tol);
        }
    }

    [Fact]
    public void MagnitudeAndFirstSampleAreKept()
    {
        Complex[] x = [new(0.3, 0.4), -2, Complex.ImaginaryOne, new(0.5, -0.5)];
        Complex[] y = Channel.PhaseNoise(x, 1e4, 1e3, 3);
        for (int i = 0; i < x.Length; i++)
            Assert.Equal(x[i].Magnitude, y[i].Magnitude, 1e-15);
        Assert.Equal(x[0], y[0]);
        Assert.Empty(Channel.PhaseNoise([], 1, 1, 0));
    }

    [Fact]
    public void TheSeedDecidesTheWalk()
    {
        Complex[] a = Channel.PhaseNoise(Ones(64), 100, 1e3, 4);
        Assert.Equal(a, Channel.PhaseNoise(Ones(64), 100, 1e3, 4));
        Assert.NotEqual(a, Channel.PhaseNoise(Ones(64), 100, 1e3, 5));
    }

    [Fact]
    public void BadArgumentsThrow()
    {
        Assert.ThrowsAny<ArgumentException>(() => Channel.PhaseNoise([Complex.One], -1, 1, 0));
        Assert.ThrowsAny<ArgumentException>(() => Channel.PhaseNoise([Complex.One], double.NaN, 1, 0));
        Assert.ThrowsAny<ArgumentException>(() => Channel.PhaseNoise([Complex.One], 1, 0, 0));
        Assert.Throws<ArgumentNullException>(() => Channel.PhaseNoise([Complex.One], 1, 1, (Random)null!));
    }
}
