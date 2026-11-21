using Xunit;

namespace SignalForge.Tests;

/// <summary>The coefficient of variation (ADR 0513).</summary>
public class CoefficientOfVariationTests
{
    [Fact]
    public void Two() =>
        Assert.Equal(0.5, Measurements.CoefficientOfVariation([3.0, 1.0]), 15);

    [Fact]
    public void NegativeValue() =>
        Assert.Equal(Math.Sqrt(6.0) / 2.0, Measurements.CoefficientOfVariation([-1.0, 2.0, 5.0]), 15);

    [Fact]
    public void RejectsAZeroMean() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.CoefficientOfVariation([1.0, -1.0]));
}
