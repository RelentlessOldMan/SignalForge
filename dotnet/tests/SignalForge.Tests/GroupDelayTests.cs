using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Group delay: against a numerical phase derivative, cascades, flat Bessel delay, errors
/// (conventions: FIR filters and IIR filters, Group delay).</summary>
public class GroupDelayTests
{
    /// <summary>−dφ/dω by a central difference of the phase, step 1e-6 of fs (independent check).</summary>
    private static double PhaseSlope(Func<double[], Complex[]> response, double f, double fs)
    {
        double d = 1e-6 * fs;
        Complex[] h = response([f - d, f + d]);
        return -(h[1] / h[0]).Phase / (2 * Math.PI * 2 * d / fs);
    }

    private static double[] Grid(double from, double to, int n) =>
        [.. Enumerable.Range(0, n).Select(i => from + (to - from) * i / (n - 1))];

    [Fact]
    public void FirMatchesThePhaseDerivative()
    {
        var rng = new Random(3);
        double[] h = [.. Enumerable.Range(0, 17).Select(_ => rng.NextDouble() - 0.5)];
        double[] f = Grid(10, 3990, 37);
        double[] tau = Dsp.FirGroupDelay(h, f, 8000);
        for (int i = 0; i < f.Length; i++)
        {
            double num = PhaseSlope(g => Dsp.FirResponse(h, g, 8000), f[i], 8000);
            Assert.True(Math.Abs(tau[i] - num) <= 1e-5 * (1 + Math.Abs(num)), $"{f[i]}: {tau[i]} vs {num}");
        }
    }

    [Fact]
    public void SosMatchesThePhaseDerivativeAndCascadesAdd()
    {
        double[][] s = Dsp.Chebyshev1Lowpass(6, 1.0, 0.2, 1.0);
        double[] f = Grid(0.001, 0.499, 41);
        double[] tau = Dsp.SosGroupDelay(s, f, 1);
        for (int i = 0; i < f.Length; i++)
        {
            double num = PhaseSlope(g => Dsp.SosResponse(s, g, 1), f[i], 1);
            Assert.True(Math.Abs(tau[i] - num) <= 1e-5 * (1 + Math.Abs(num)), $"{f[i]}: {tau[i]} vs {num}");
            double parts = s.Sum(row => Dsp.SosGroupDelay([row], [f[i]], 1)[0]);
            Assert.True(Math.Abs(tau[i] - parts) <= 1e-12 * (1 + Math.Abs(parts)));
        }
    }

    [Fact]
    public void LinearPhaseTapsDelayHalfTheirLength()
    {
        double[] h = Dsp.FirLowpass(41, 0.1, 1);
        foreach (double t in Dsp.FirGroupDelay(h, Grid(0, 0.09, 10), 1))
            Assert.True(Math.Abs(t - 20) < 1e-9);
    }

    [Fact]
    public void BesselDelayIsFlatWhereButterworthIsNot()
    {
        double[] f = Grid(0, 0.05, 11);
        double[] bessel = Dsp.SosGroupDelay(Dsp.BesselLowpass(5, 0.05, 1), f, 1);
        double[] butter = Dsp.SosGroupDelay(Dsp.ButterworthLowpass(5, 0.05, 1), f, 1);
        Assert.True(bessel.Take(6).Max(t => Math.Abs(t / bessel[0] - 1)) < 0.01);
        Assert.True(bessel.Max() / bessel.Min() < 1.03);
        Assert.True(butter.Max() / butter.Min() > 1.3);
    }

    [Fact]
    public void NanOnlyAtTheZero()
    {
        double[] tau = Dsp.SosGroupDelay([[1, 1, 0, 1, 0, 0]], [0.49, 0.5], 1);
        Assert.Equal(0.5, tau[0], 12);
        Assert.True(double.IsNaN(tau[1]));
    }

    [Fact]
    public void BadArgumentsThrow()
    {
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirGroupDelay([], [0.0], 1));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirGroupDelay([1.0], [double.NaN], 1));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirGroupDelay([1.0], [0.0], 0));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.SosGroupDelay([[1, 0, 0, 0, 0, 0]], [0.0], 1));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.SosGroupDelay([[1, 0, 0, 1, 0]], [0.0], 1));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.SosGroupDelay([[1, 0, 0, 1, 0, 0]], [double.PositiveInfinity], 1));
    }
}
