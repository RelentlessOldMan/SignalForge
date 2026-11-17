using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Farrow variable delay (ADR 0226).</summary>
public class FarrowDelayTests
{
    [Fact]
    public void MatchesLagrangeFirPerSample()
    {
        var rng = new Random(5);
        Complex[] x = [.. Enumerable.Range(0, 40).Select(_ => new Complex(rng.NextDouble() - 0.5, rng.NextDouble() - 0.5))];
        double[] d = [.. Enumerable.Range(0, 40).Select(_ => 2.0 + 3.0 * rng.NextDouble())];
        for (int order = 1; order <= 5; order++)
        {
            Complex[] y = Channel.FarrowDelay(x, d, order);
            double half = (order - 1) / 2.0;
            for (int i = 0; i < 40; i++)
            {
                double q = i - d[i] - half;
                int b = (int)Math.Floor(q);
                double u = q - b + half;
                double[] h = Dsp.LagrangeFir(order - u, order);
                Complex want = Complex.Zero;
                for (int k = 0; k <= order; k++)
                {
                    int m = b + order - k;
                    if (m >= 0 && m < 40)
                        want += h[k] * x[m];
                }
                Assert.True(Complex.Abs(y[i] - want) < 1e-11, $"order {order}, sample {i}");
            }
        }
    }
}
