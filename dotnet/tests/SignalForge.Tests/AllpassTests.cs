using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>All-pass sections: unit magnitude, the named phases, and the total phase as the group
/// delay's integral (conventions: IIR filters, All-pass sections).</summary>
public class AllpassTests
{
    private static double[] Phase(double[][] sos, double[] f)
    {
        Complex[] h = Dsp.SosResponse(sos, f, 1);
        double[] p = new double[f.Length];
        for (int i = 0; i < f.Length; i++)
        {
            p[i] = h[i].Phase;
            if (i > 0)
                p[i] -= 2 * Math.PI * Math.Round((p[i] - p[i - 1]) / (2 * Math.PI));
        }
        return p;
    }

    private static double[] Grid(double hi, int n) => [.. Enumerable.Range(0, n).Select(i => hi * i / (n - 1))];

    [Theory]
    [InlineData(0.01)]
    [InlineData(0.1)]
    [InlineData(0.25)]
    [InlineData(0.4)]
    [InlineData(0.49)]
    public void FirstOrderIsMinusAQuarterTurnAtTheCutoff(double cutoff)
    {
        double[][] sos = Dsp.AllpassFirstOrder(cutoff, 1);
        double[] p = Phase(sos, Grid(0.5, 2001));
        Assert.Equal(0, p[0]);
        for (int i = 1; i < p.Length; i++)
            Assert.True(p[i] < p[i - 1]);
        Complex h = Dsp.SosResponse(sos, [cutoff], 1)[0];
        Assert.True(Complex.Abs(h + Complex.ImaginaryOne) < 1e-12, $"{h}");
        foreach (Complex v in Dsp.SosResponse(sos, Grid(0.5, 101), 1))
            Assert.Equal(1, v.Magnitude, 1e-13);
    }

    [Theory]
    [InlineData(0.1, 0.05)]
    [InlineData(0.3, 0.02)]
    [InlineData(0.25, 0.2)]
    [InlineData(0.05, 0.08)]
    [InlineData(0.45, 0.4)]
    public void SecondOrderPhasePointsAreABandwidthApart(double center, double bandwidth)
    {
        double[][] sos = Dsp.AllpassSecondOrder(center, bandwidth, 1);
        double[] f = Grid(0.5, 200001);
        double[] p = Phase(sos, f);
        Assert.Equal(-2 * Math.PI, p[^1], 1e-9);
        double At(double phase)
        {
            int i = Array.FindIndex(p, v => v <= phase);
            return f[i - 1] + (f[i] - f[i - 1]) * (p[i - 1] - phase) / (p[i - 1] - p[i]);
        }
        Assert.Equal(center, At(-Math.PI), 1e-6);
        Assert.Equal(bandwidth, At(-1.5 * Math.PI) - At(-0.5 * Math.PI), 1e-6);
        foreach (Complex v in Dsp.SosResponse(sos, Grid(0.5, 101), 1))
            Assert.Equal(1, v.Magnitude, 1e-13);
    }

    [Fact]
    public void GroupDelayIntegratesToTheTotalPhase()
    {
        double[] f = Grid(0.5, 100001);
        foreach (var (sos, turns) in new[] { (Dsp.AllpassFirstOrder(0.2, 1), 0.5), (Dsp.AllpassSecondOrder(0.15, 0.1, 1), 1.0) })
        {
            double[] tau = Dsp.SosGroupDelay(sos, f, 1);
            double total = 0;
            for (int i = 1; i < f.Length; i++)
                total += (tau[i] + tau[i - 1]) / 2 * (f[i] - f[i - 1]);
            Assert.True(Math.Abs(total * 2 * Math.PI / (2 * Math.PI * turns) - 1) < 1e-8, $"{total}");
        }
    }

    [Fact]
    public void BadArgumentsThrow()
    {
        Assert.ThrowsAny<ArgumentException>(() => Dsp.AllpassFirstOrder(0, 1));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.AllpassFirstOrder(0.5, 1));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.AllpassFirstOrder(double.NaN, 1));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.AllpassSecondOrder(0.1, 0, 1));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.AllpassSecondOrder(0.1, 0.5, 1));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.AllpassSecondOrder(0.5, 0.1, 1));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.AllpassSecondOrder(0.1, 0.1, -1));
    }
}
