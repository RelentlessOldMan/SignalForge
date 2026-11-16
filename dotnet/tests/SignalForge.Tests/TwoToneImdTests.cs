using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Two-tone third-order intermodulation and IP3 (conventions: Two-tone
/// intermodulation; ADR 0107).</summary>
public class TwoToneImdTests
{
    private const int N = 4096;

    private static double[] TwoTones(double a, int k1, int k2) =>
        [.. Enumerable.Range(0, N).Select(n => a * (Math.Cos(2 * Math.PI * k1 * n / N) + Math.Cos(2 * Math.PI * k2 * n / N)))];

    private static double[] Cubic(double[] x, double a3) => [.. x.Select(v => v + a3 * v * v * v)];

    [Theory]
    [InlineData(0.02)]
    [InlineData(-0.3)]
    [InlineData(1.5)]
    public void SmallDriveExtrapolatesToTheTextbookIntercept(double a3)
    {
        TwoToneImd r = Measurements.TwoToneImd(Cubic(TwoTones(1e-3, 400, 433), a3), N, 400, 433);
        double want = 10 * Math.Log10(4 / (3 * Math.Abs(a3)) / 2);
        Assert.True(Math.Abs(r.Ip3Db - want) < 2e-4, $"{r.Ip3Db} vs {want}");
        Assert.True(Math.Abs(r.ImdDbc[0] - r.ImdDbc[1]) < 1e-4);
        Assert.Equal([367.0, 466.0], r.ImdFrequencies);
        Assert.Equal(400, r.ToneFrequencies[0], 6);
        Assert.Equal(433, r.ToneFrequencies[1], 6);
    }

    [Fact]
    public void InterceptStaysPutAsDriveRises()
    {
        TwoToneImd a = Measurements.TwoToneImd(Cubic(TwoTones(0.01, 300, 340), 0.1), N, 300, 340);
        TwoToneImd b = Measurements.TwoToneImd(Cubic(TwoTones(0.01 * Math.Pow(10, 1 / 20.0), 300, 340), 0.1), N, 300, 340);
        Assert.True(Math.Abs(b.WorstImdDbc - a.WorstImdDbc - 2) < 1e-3);
        Assert.True(Math.Abs(b.Ip3Db - a.Ip3Db) < 1e-3);
    }

    [Fact]
    public void ALinearDeviceHasNoProducts()
    {
        TwoToneImd r = Measurements.TwoToneImd(TwoTones(1, 100, 150), N, 100, 150);
        Assert.All(r.ImdPowers, p => Assert.Equal(0, p));
        Assert.All(r.ImdDbc, d => Assert.Equal(double.NegativeInfinity, d));
        Assert.Equal(double.PositiveInfinity, r.Ip3Db);
        Assert.All(r.TonePowers, p => Assert.Equal(0.5, p, 12));
    }

    [Fact]
    public void ComplexProductsWrap()
    {
        Complex[] x = [.. Enumerable.Range(0, N).Select(n =>
            0.3 * (Complex.FromPolarCoordinates(1, -2 * Math.PI * 1800 * n / N) + Complex.FromPolarCoordinates(1, 2 * Math.PI * 1900 * n / N)))];
        Complex[] y = [.. x.Select(z => z + 0.5 * z.Magnitude * z.Magnitude * z)];
        TwoToneImd r = Measurements.TwoToneImd(y, N, -1800, 1900);
        Assert.Equal([-1404.0, 1504.0], r.ImdFrequencies);
        double want = Math.Pow(0.5 * 0.027, 2);
        Assert.All(r.ImdPowers, p => Assert.True(Math.Abs(p - want) < 1e-9 * want));
    }

    [Theory]
    [InlineData(433.0, 400.0)]
    [InlineData(400.0, double.NaN)]
    [InlineData(double.PositiveInfinity, 433.0)]
    [InlineData(400.0, 2049.0)]
    [InlineData(400.0, 402.0)]
    public void BadArguments(double f1, double f2) =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.TwoToneImd(TwoTones(1, 400, 433), N, f1, f2));
}
