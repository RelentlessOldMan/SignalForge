using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Power CCDF (conventions: Power CCDF; ADR 0119).</summary>
public class PowerCcdfTests
{
    private const int N = 200_000;
    private static readonly double[] Levels = [-10, -3, 0, 3, 6, 9];
    // erfc(√(g/2)) at each level, from Python's math.erfc
    private static readonly double[] RealReference =
        [0.7518296340458492, 0.47897892605179715, 0.31731050786291404, 0.15779174396344883,
         0.04601427775573203, 0.004826620839267728];
    private static readonly double[] ToneLevels = [0.01, 1, 3];
    private static readonly double[] Probabilities = [1e-3, 0.01, 0.1, 0.5];

    private static double Gauss(Random rng) =>
        Math.Sqrt(-2 * Math.Log(1 - rng.NextDouble())) * Math.Cos(2 * Math.PI * rng.NextDouble());

    // five binomial sigmas, plus five sigmas of the sample mean moving the threshold
    private static double Tolerance(double p, double g) =>
        5 * Math.Sqrt(p * (1 - p) / N) + 5 * g * p / Math.Sqrt(N) + 2.0 / N;

    [Fact]
    public void ComplexGaussianNoiseIsExponential()
    {
        var rng = new Random(119);
        var x = new Complex[N];
        for (int i = 0; i < N; i++)
            x[i] = new Complex(Gauss(rng), Gauss(rng));
        var r = Measurements.PowerCcdf(x, Levels);
        for (int i = 0; i < Levels.Length; i++)
        {
            double g = Math.Pow(10, Levels[i] / 10), want = Math.Exp(-g);
            Assert.True(Math.Abs(r.Probabilities[i] - want) <= Tolerance(want, g), $"{Levels[i]} dB");
        }
    }

    [Fact]
    public void RealGaussianNoiseIsChiSquareOne()
    {
        var rng = new Random(1190);
        var x = new double[N];
        for (int i = 0; i < N; i++)
            x[i] = Gauss(rng);
        var r = Measurements.PowerCcdf(x, Levels);
        for (int i = 0; i < Levels.Length; i++)
        {
            double g = Math.Pow(10, Levels[i] / 10), want = RealReference[i];
            Assert.True(Math.Abs(r.Probabilities[i] - want) <= Tolerance(want, g), $"{Levels[i]} dB");
        }
    }

    [Fact]
    public void AComplexToneNeverExceedsItsMean()
    {
        var x = new Complex[1000];
        for (int n = 0; n < x.Length; n++)
            x[n] = 3 * Complex.Exp(new Complex(0, 2 * Math.PI * 0.123 * n));
        var r = Measurements.PowerCcdf(x, ToneLevels);
        Assert.All(r.Probabilities, p => Assert.Equal(0, p));
        Assert.Equal(9, r.MeanPower, 1e-11);
    }

    [Fact]
    public void LevelAndCcdfAreInverses()
    {
        var rng = new Random(11);
        var x = new Complex[5000];
        for (int i = 0; i < x.Length; i++)
            x[i] = new Complex(Gauss(rng), Gauss(rng));
        foreach (double q in Probabilities)
        {
            double lv = Measurements.PowerCcdfLevel(x, q);
            // the threshold goes back through dB, so it is the same only up to rounding
            Assert.True(Measurements.PowerCcdf(x, [lv + 1e-9]).Probabilities[0] <= q);
            Assert.True(Measurements.PowerCcdf(x, [lv - 1e-9]).Probabilities[0] > q);
        }
    }

    [Fact]
    public void LevelBelowOneSampleIsThePapr()
    {
        var rng = new Random(12);
        var x = new double[777];
        for (int i = 0; i < x.Length; i++)
            x[i] = Gauss(rng);
        Assert.Equal(Measurements.PowerStats(x).PaprDb, Measurements.PowerCcdfLevel(x, 1e-4), 1e-12);
    }

    [Theory]
    [InlineData(0.0)]
    [InlineData(1.0)]
    [InlineData(-0.1)]
    [InlineData(double.NaN)]
    public void BadProbability(double q) =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.PowerCcdfLevel([1.0, 2.0], q));
}
