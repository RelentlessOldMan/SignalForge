using Xunit;

namespace SignalForge.Tests;

/// <summary>Lagrange fractional-delay FIR (ADR 0225).</summary>
public class LagrangeFirTests
{
    [Fact]
    public void MomentsMatchTheDelay()
    {
        double d = 2.37;
        double[] h = Dsp.LagrangeFir(d, 5);
        for (int q = 0; q <= 5; q++)
        {
            double moment = 0;
            for (int k = 0; k < h.Length; k++)
                moment += h[k] * Math.Pow(k, q);
            Assert.Equal(Math.Pow(d, q), moment, 1e-9);
        }
    }
}
