using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Itakura-Saito distance between AR models (ADR 0217).</summary>
public class ItakuraSaitoTests
{
    [Fact]
    public void MatchesTheSampledSpectra()
    {
        double[] reference = Dsp.ReflectionToLpc([0.6, -0.4, 0.3]);
        double[] test = Dsp.ReflectionToLpc([-0.5, 0.2]);
        const int n = 8192;
        double total = 0;
        for (int i = 0; i < n; i++)
        {
            double w = 2 * Math.PI * i / n;
            double ratio = (1.3 / Response(reference, w)) / (0.7 / Response(test, w));
            total += ratio - Math.Log(ratio) - 1;
        }
        Assert.Equal(total / n, Dsp.ItakuraSaito(reference, 1.3, test, 0.7), 1e-10);
    }

    private static double Response(double[] a, double w)
    {
        Complex h = Complex.Zero;
        for (int j = 0; j < a.Length; j++)
            h += a[j] * Complex.Exp(new Complex(0, -w * j));
        return (h.Real * h.Real) + (h.Imaginary * h.Imaginary);
    }
}
