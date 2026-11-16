using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Two-tone second-order intermodulation and IP2 (conventions: Two-tone
/// intermodulation; ADR 0110).</summary>
public class TwoToneIp2Tests
{
    private const int N = 4096;
    private static readonly double[] Drives = [1e-3, 1e-2, 1e-1];

    private static double[] TwoTones(double a, int k1, int k2) =>
        [.. Enumerable.Range(0, N).Select(n => a * (Math.Cos(2 * Math.PI * k1 * n / N) + Math.Cos(2 * Math.PI * k2 * n / N)))];

    private static double[] Poly(double[] x, double a2, double a3) => [.. x.Select(v => v + a2 * v * v + a3 * v * v * v)];

    [Theory]
    [InlineData(0.01)]
    [InlineData(-0.5)]
    [InlineData(3.0)]
    public void SmallDriveExtrapolatesToTheTextbookIntercept(double a2)
    {
        // y = x + a2 x^2: the products are exactly a2 A^2 at any drive, so IP2 is A_IP2 = 1/|a2|
        TwoToneIp2 r = Measurements.TwoToneIp2(Poly(TwoTones(1e-3, 400, 433), a2, 0), N, 400, 433);
        Assert.Equal(10 * Math.Log10(1 / (2 * a2 * a2)), r.Ip2Db, 9);
        Assert.Equal(r.ImdDbc[0], r.ImdDbc[1], 9);
        Assert.Equal([33.0, 833.0], r.ImdFrequencies);
    }

    [Fact]
    public void TheInterceptDoesNotMoveWithDrive()
    {
        // slope 2 against slope 1: every 1 dB of drive moves the products 2 dB and IP2 not at all
        double[] got = [.. Drives.Select(a => Measurements.TwoToneIp2(Poly(TwoTones(a, 400, 433), 0.2, 0), N, 400, 433).Ip2Db)];
        foreach (double g in got)
            Assert.Equal(got[0], g, 9);
    }

    [Fact]
    public void OddOrderOnlyHasNoSecondOrderProducts()
    {
        TwoToneIp2 r = Measurements.TwoToneIp2(Poly(TwoTones(0.5, 400, 433), 0, 0.1), N, 400, 433);
        Assert.True(r.WorstImdDbc < -200, $"{r.WorstImdDbc}"); // rounding only: a cubic makes no sum or difference line
        Assert.True(r.Ip2Db > 50);
    }

    [Fact]
    public void ComplexEnvelopeSquareHasNoSumProduct()
    {
        // y = x + a2 |x|^2 has lines at +-(f2 - f1) and DC, none at f1 + f2
        Complex[] x = [.. Enumerable.Range(0, N).Select(n => 0.5 * (Complex.FromPolarCoordinates(1, 2 * Math.PI * -300 * n / N) + Complex.FromPolarCoordinates(1, 2 * Math.PI * 500 * n / N)))];
        Complex[] y = [.. x.Select(z => z + 0.2 * z.Magnitude * z.Magnitude)];
        TwoToneIp2 r = Measurements.TwoToneIp2(y, N, -300, 500);
        Assert.Equal(double.NegativeInfinity, r.ImdDbc[1]);
        Assert.Equal(10 * Math.Log10(0.05 * 0.05 / 0.25), r.ImdDbc[0], 9);
    }
}
