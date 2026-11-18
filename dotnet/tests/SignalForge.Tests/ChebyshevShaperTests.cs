using Xunit;

namespace SignalForge.Tests;

/// <summary>Chebyshev waveshaper (ADR 0321).</summary>
public class ChebyshevShaperTests
{
    [Fact]
    public void TheThirdPolynomialIsFourXCubedLessThreeX()
    {
        double[] x = [-1, -0.5, 0.3, 0.8, 1];
        double[] y = Dsp.ChebyshevShaper(x, [0, 0, 0, 1]);
        for (int n = 0; n < x.Length; n++)
            Assert.Equal((4 * x[n] * x[n] * x[n]) - (3 * x[n]), y[n], 1e-15);
    }

    [Fact]
    public void OneWeightIsAConstant() => Assert.Equal([0.75, 0.75], Dsp.ChebyshevShaper([0.25, -0.5], [0.75]));

    [Fact]
    public void RejectsASampleAboveOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.ChebyshevShaper([1.5], [1.0]));
}
