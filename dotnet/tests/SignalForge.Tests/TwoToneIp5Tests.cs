using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Two-tone fifth-order intermodulation and IP5 (conventions: Two-tone
/// intermodulation; ADR 0117).</summary>
public class TwoToneIp5Tests
{
    private const int N = 4096;

    private static double[] TwoTones(double a, int k1, int k2) =>
        [.. Enumerable.Range(0, N).Select(n => a * (Math.Cos(2 * Math.PI * k1 * n / N) + Math.Cos(2 * Math.PI * k2 * n / N)))];

    private static double[] Poly(double[] x, double a3, double a5) => [.. x.Select(v => v + a3 * v * v * v + a5 * Math.Pow(v, 5))];

    [Theory]
    [InlineData(0.01, 0.1)]
    [InlineData(-0.5, 0.1)]
    [InlineData(3.0, 0.1)]
    [InlineData(0.01, 0.3)]
    [InlineData(-0.5, 0.3)]
    [InlineData(3.0, 0.3)]
    public void TheInterceptMatchesTheExpansion(double a5, double a)
    {
        // y = x + a5 x^5 on equal tones: products (5/8) a5 A^5, tones A(1 + 6.25 a5 A^4)
        TwoToneIp5 r = Measurements.TwoToneIp5(Poly(TwoTones(a, 400, 433), 0, a5), N, 400, 433);
        double pt = Math.Pow(a * (1 + 6.25 * a5 * Math.Pow(a, 4)), 2) / 2, p5 = Math.Pow(5.0 / 8 * a5 * Math.Pow(a, 5), 2) / 2;
        Assert.Equal((50 * Math.Log10(pt) - 10 * Math.Log10(p5)) / 4, r.Ip5Db, 1e-8);
        Assert.Equal(r.ImdDbc[0], r.ImdDbc[1], 1e-6);
        Assert.Equal([334.0, 499.0], r.ImdFrequencies);
    }

    [Fact]
    public void SmallDriveTendsToTheTextbookIntercept()
    {
        // A_IP5^4 = 8/(5|a5|); the tones' growth moves it by about 1.4e-3 dB at this drive
        TwoToneIp5 r = Measurements.TwoToneIp5(Poly(TwoTones(0.1, 400, 433), 0, 0.2), N, 400, 433);
        Assert.Equal(10 * Math.Log10(Math.Sqrt(8 / (5 * 0.2)) / 2), r.Ip5Db, 2e-3);
    }

    [Fact]
    public void ACubicHasNoFifthOrderProducts()
    {
        TwoToneIp5 r = Measurements.TwoToneIp5(Poly(TwoTones(0.5, 400, 433), 0.1, 0), N, 400, 433);
        Assert.True(r.WorstImdDbc < -200);
    }

    [Fact]
    public void ComplexEnvelopeQuintic()
    {
        const double a = 0.3, a5 = 0.2;
        Complex[] x = [.. Enumerable.Range(0, N).Select(n =>
            a * (Complex.FromPolarCoordinates(1, 2 * Math.PI * -300 * n / N) + Complex.FromPolarCoordinates(1, 2 * Math.PI * 200 * n / N)))];
        Complex[] y = [.. x.Select(v => v + a5 * Math.Pow(v.Magnitude, 4) * v)];
        TwoToneIp5 r = Measurements.TwoToneIp5(y, N, -300, 200);
        double pt = Math.Pow(a * (1 + 10 * a5 * Math.Pow(a, 4)), 2), p5 = Math.Pow(a5 * Math.Pow(a, 5), 2);
        Assert.Equal([-1300.0, 1200.0], r.ImdFrequencies);
        Assert.Equal((5 * 10 * Math.Log10(pt) - 10 * Math.Log10(p5)) / 4, r.Ip5Db, 1e-9);
    }
}
