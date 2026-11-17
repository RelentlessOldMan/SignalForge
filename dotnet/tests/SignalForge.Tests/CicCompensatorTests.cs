using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>CIC droop compensator (ADR 0232).</summary>
public class CicCompensatorTests
{
    [Fact]
    public void FlattensTheCicPassbandOnTheGrid()
    {
        int r = 8, n = 4, t = 31, c = 15;
        double[] h = Dsp.CicCompensator(r, n, t, 0.25, 1.0);
        double[] taps = Dsp.CicTaps(r, n);
        for (int j = 0; j <= (int)(0.25 * t); j++)
        {
            double f = (double)j / t;
            Complex cic = Complex.Zero, comp = Complex.Zero;
            for (int k = 0; k < taps.Length; k++)
                cic += taps[k] * Complex.Exp(new Complex(0, -2 * Math.PI * f / r * k));
            for (int k = 0; k < t; k++)
                comp += h[k] * Complex.Exp(new Complex(0, -2 * Math.PI * f * (k - c)));
            Assert.True(Math.Abs(Complex.Abs(cic) / Math.Pow(r, n) * comp.Real - 1.0) < 1e-10, $"bin {j}");
        }
    }
}
