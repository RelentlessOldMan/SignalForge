using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Thiran allpass (ADR 0227).</summary>
public class ThiranAllpassTests
{
    private static Complex Response(double[] a, double w)
    {
        Complex num = Complex.Zero, den = Complex.Zero;
        for (int k = 0; k < a.Length; k++)
        {
            Complex e = Complex.FromPolarCoordinates(1, -w * k);
            num += a[a.Length - 1 - k] * e;
            den += a[k] * e;
        }
        return num / den;
    }

    [Fact]
    public void UnitMagnitudeAndDcGroupDelay()
    {
        double d = 2.4;
        double[] a = Dsp.ThiranAllpass(d, 3);
        for (double w = 0.05; w < 3.1; w += 0.25)
            Assert.Equal(1.0, Complex.Abs(Response(a, w)), 1e-12);
        double h = 1e-4;
        double delay = -(Response(a, 2 * h).Phase - Response(a, h).Phase) / h;
        Assert.Equal(d, delay, 1e-6);
    }
}
