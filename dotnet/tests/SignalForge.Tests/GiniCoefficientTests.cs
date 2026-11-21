using Xunit;

namespace SignalForge.Tests;

/// <summary>The Gini coefficient (ADR 0510).</summary>
public class GiniCoefficientTests
{
    [Fact]
    public void Ramp() =>
        Assert.Equal(0.25, Measurements.GiniCoefficient([4.0, 1.0, 3.0, 2.0]), 15);

    [Fact]
    public void OneHoldsAll() =>
        Assert.Equal(0.75, Measurements.GiniCoefficient([0.0, 4.0, 0.0, 0.0]), 15);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.GiniCoefficient([0.0, 0.0]));

    [Fact]
    public void RejectsANegativeValue() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.GiniCoefficient([1.0, -1.0]));
}
