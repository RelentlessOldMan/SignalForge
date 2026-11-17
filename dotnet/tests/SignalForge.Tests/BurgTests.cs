using Xunit;

namespace SignalForge.Tests;

/// <summary>Burg AR fit (conventions: Burg AR fit; ADR 0205).</summary>
public class BurgTests
{
    [Fact]
    public void RecoversARealAr1Model()
    {
        var rng = new Random(54);
        var x = new double[20000];
        for (int i = 1; i < x.Length; i++)
        {
            double u1 = 1.0 - rng.NextDouble(), u2 = rng.NextDouble();
            x[i] = (0.7 * x[i - 1]) + (Math.Sqrt(-2 * Math.Log(u1)) * Math.Cos(2 * Math.PI * u2));
        }
        var fit = Dsp.Burg(x, 1);
        Assert.Equal(-0.7, fit.Coefficients[1], 0.02);
        Assert.Equal(1.0, fit.Error, 0.05);
    }
}
