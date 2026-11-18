using Xunit;

namespace SignalForge.Tests;

/// <summary>Hjorth parameters (ADR 0324).</summary>
public class HjorthParametersTests
{
    [Fact]
    public void AlternatingSignsByHand()
    {
        // d = (−2, 2, −2, 2, −2): mean −2/5, var 96/25; dd = ±4, var 16.
        HjorthParameters h = Measurements.HjorthParameters([1.0, -1.0, 1.0, -1.0, 1.0, -1.0]);
        Assert.Equal(1.0, h.Activity, 1e-15);
        Assert.Equal(Math.Sqrt(3.84), h.Mobility, 1e-15);
        Assert.Equal(25.0 / 24, h.Complexity, 1e-14);
    }

    [Fact]
    public void ASineHasComplexityOne()
    {
        double w = 2 * Math.PI / 50;
        double[] x = new double[5000];
        for (int n = 0; n < x.Length; n++)
            x[n] = Math.Sin(w * n);
        HjorthParameters h = Measurements.HjorthParameters(x);
        Assert.Equal(2 * Math.Sin(w / 2), h.Mobility, 1e-3);
        Assert.Equal(1.0, h.Complexity, 1e-3);
    }

    [Fact]
    public void RejectsARamp() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HjorthParameters([0.0, 1.0, 2.0]));
}
