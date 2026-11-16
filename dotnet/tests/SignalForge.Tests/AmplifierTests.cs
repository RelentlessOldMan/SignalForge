using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Saleh and Rapp amplifier models (conventions: Channel, Amplifier models; ADR 0114).</summary>
public class AmplifierTests
{
    private const double Aa = 2.1587, Ba = 1.1517, Ap = 4.0033, Bp = 9.1040;

    private static (double[] Edges, Complex[] X) Sweep(double loDb, int bins, double step)
    {
        double[] edges = [.. Enumerable.Range(0, bins + 1).Select(i => loDb + step * i)];
        double[] th = [0.2, 1.9, -2.4];
        Complex[] x = [.. Enumerable.Range(0, bins).SelectMany(i =>
            th.Select(t => Complex.FromPolarCoordinates(Math.Pow(10, (edges[i] + edges[i + 1]) / 2 / 20), t)))];
        return (edges, x);
    }

    [Fact]
    public void AmAmPmReadsTheSalehCurvesBack()
    {
        var (edges, x) = Sweep(-30.0, 80, 0.5);
        AmAmPm r = Measurements.AmAmPm(x, Channel.SalehAmplifier(x, Aa, Ba, Ap, Bp), edges);
        for (int i = 0; i < r.LevelsDb.Length; i++)
        {
            double rad = Math.Pow(10, r.LevelsDb[i] / 20);
            Assert.Equal(20 * Math.Log10(Aa / (1 + Ba * rad * rad)), r.GainDb[i], 1e-10);
            Assert.Equal(Ap * rad * rad / (1 + Bp * rad * rad) * 180 / Math.PI, r.PhaseDeg[i], 1e-10);
        }
    }

    [Theory]
    [InlineData(0.5)]
    [InlineData(1.0)]
    [InlineData(2.0)]
    [InlineData(5.0)]
    public void GainCompressionFindsRappsOneDbPoint(double p)
    {
        const double g = 3.0, aSat = 0.5;
        var (edges, x) = Sweep(-160.0, 9000, 0.02);
        AmAmPm r = Measurements.AmAmPm(x, Channel.RappAmplifier(x, g, aSat, p), edges);
        GainCompression c = Measurements.GainCompression(r.LevelsDb, [.. r.LevelsDb.Zip(r.GainDb, (l, gdb) => l + gdb)]);
        double expected = 20 * Math.Log10(aSat / g * Math.Pow(Math.Pow(10, p / 10) - 1, 1 / (2 * p)));
        Assert.Equal(expected, c.InputPointDb, 1e-3);
        Assert.Equal(20 * Math.Log10(g), c.SmallSignalGainDb, 1e-5);
    }

    [Fact]
    public void RappIsContinuousAtTheKneeAndSaturates()
    {
        const double g = 2.0, aSat = 1.0, p = 1.5;
        double knee = aSat / g;
        Complex[] y = Channel.RappAmplifier([knee * (1 - 1e-12), knee, knee * (1 + 1e-12)], g, aSat, p);
        Assert.All(y, v => Assert.Equal(aSat / Math.Pow(2, 1 / (2 * p)), Complex.Abs(v), 1e-11));
        Complex[] big = Channel.RappAmplifier([new Complex(0, 1e200), new Complex(-1e300, 0)], g, aSat, p);
        Assert.Equal(new Complex(0, aSat), big[0]);
        Assert.Equal(new Complex(-aSat, 0), big[1]);
    }

    [Fact]
    public void ZeroStaysZeroAndEmptyStaysEmpty()
    {
        Assert.Equal(Complex.Zero, Channel.SalehAmplifier([Complex.Zero], Aa, Ba, Ap, Bp)[0]);
        Assert.Equal(Complex.Zero, Channel.RappAmplifier([Complex.Zero], 1, 1, 1)[0]);
        Assert.Empty(Channel.RappAmplifier([], 1, 1, 1));
    }

    [Theory]
    [InlineData(0.0, 1.0, 1.0, 1.0)]
    [InlineData(1.0, -1.0, 1.0, 1.0)]
    [InlineData(1.0, 1.0, 1.0, -1.0)]
    [InlineData(1.0, 1.0, double.PositiveInfinity, 1.0)]
    [InlineData(1.0, double.NaN, 1.0, 1.0)]
    public void SalehBadArgumentsThrow(double aa, double ba, double ap, double bp) =>
        Assert.ThrowsAny<ArgumentException>(() => Channel.SalehAmplifier([Complex.One], aa, ba, ap, bp));

    [Theory]
    [InlineData(0.0, 1.0, 1.0)]
    [InlineData(1.0, -1.0, 1.0)]
    [InlineData(1.0, 1.0, 0.0)]
    [InlineData(1.0, 1.0, double.NaN)]
    public void RappBadArgumentsThrow(double g, double aSat, double p) =>
        Assert.ThrowsAny<ArgumentException>(() => Channel.RappAmplifier([Complex.One], g, aSat, p));
}
