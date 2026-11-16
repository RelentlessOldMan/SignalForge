using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>AM/AM and AM/PM by input-level bin (conventions: AM/AM and AM/PM; ADR 0113).</summary>
public class AmAmPmTests
{
    [Fact]
    public void ALinearGainWithAFixedPhaseReadsFlatCurves()
    {
        var rng = new Random(3);
        Complex[] x = [.. Enumerable.Range(0, 5000).Select(_ => new Complex(rng.NextDouble() * 4 - 2, rng.NextDouble() * 4 - 2))];
        Complex g = Complex.FromPolarCoordinates(3.0, -40.0 * Math.PI / 180);
        double[] edges = [.. Enumerable.Range(0, 15).Select(i => -30.0 + 3 * i)];
        AmAmPm r = Measurements.AmAmPm(x, [.. x.Select(v => g * v)], edges);
        for (int i = 0; i < r.Counts.Length; i++)
        {
            if (r.Counts[i] == 0)
                continue;
            Assert.Equal(20 * Math.Log10(3.0), r.GainDb[i], 1e-12);
            Assert.Equal(-40.0, r.PhaseDeg[i], 1e-10);
        }
    }

    [Theory]
    [InlineData(1.0)]
    [InlineData(2.0)]
    [InlineData(3.0)]
    public void ARappLimiterThroughGainCompressionFindsItsPoint(double p)
    {
        // A(r) = r / (1 + (r/s)^(2p))^(1/(2p)): 1 dB down where (r/s)^(2p) = 10^(2p/20) - 1
        const double s = 0.8;
        double[] edges = [.. Enumerable.Range(0, 9001).Select(i => -80.0 + 0.01 * i)];
        var x = new List<Complex>();
        for (int i = 0; i < edges.Length - 1; i++)
        {
            double rad = Math.Pow(10, (edges[i] + edges[i + 1]) / 2 / 20);
            for (int k = 0; k < 4; k++)
                x.Add(Complex.FromPolarCoordinates(rad, k * Math.PI / 2));
        }
        Complex[] y = [.. x.Select(v => v / Math.Pow(1 + Math.Pow(Complex.Abs(v) / s, 2 * p), 1 / (2 * p)))];
        AmAmPm r = Measurements.AmAmPm([.. x], y, edges);
        Assert.All(r.Counts, n => Assert.Equal(4, n));
        GainCompression c = Measurements.GainCompression(r.LevelsDb, [.. r.LevelsDb.Zip(r.GainDb, (l, gdb) => l + gdb)]);
        double expected = 20 * Math.Log10(s * Math.Pow(Math.Pow(10, 2 * p / 20) - 1, 1 / (2 * p)));
        Assert.Equal(expected, c.InputPointDb, 1e-4);
    }

    [Fact]
    public void BadArgumentsThrow()
    {
        Complex[] one = [Complex.One];
        Assert.ThrowsAny<ArgumentException>(() => Measurements.AmAmPm(one, [Complex.One, Complex.One], [0.0, 1.0]));
        Assert.ThrowsAny<ArgumentException>(() => Measurements.AmAmPm([], [], [0.0, 1.0]));
        Assert.ThrowsAny<ArgumentException>(() => Measurements.AmAmPm(one, one, [0.0]));
        Assert.ThrowsAny<ArgumentException>(() => Measurements.AmAmPm(one, one, [1.0, 0.0]));
        Assert.ThrowsAny<ArgumentException>(() => Measurements.AmAmPm([new Complex(double.NaN, 0)], one, [0.0, 1.0]));
    }
}
