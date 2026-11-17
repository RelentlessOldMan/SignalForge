using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Farrow resampler (ADR 0228).</summary>
public class FarrowResampleTests
{
    [Fact]
    public void SineResampled()
    {
        Complex[] x = [.. Enumerable.Range(0, 400).Select(n => new Complex(Math.Sin(2 * Math.PI * 0.01 * n), 0))];
        Complex[] y = Channel.FarrowResample(x, 1.5, 5);
        Assert.Equal(599, y.Length);
        for (int k = 0; k < y.Length; k++)
        {
            double t = k / 1.5;
            if (t > 3 && t < 396)
                Assert.True(Complex.Abs(y[k] - Math.Sin(2 * Math.PI * 0.01 * t)) < 1e-6, $"output {k}");
        }
    }
}
