using Xunit;

namespace SignalForge.Tests;

/// <summary>The abundance-gradient part of the Bray-Curtis dissimilarity (ADR 0583).</summary>
public class BrayCurtisGradientTests
{
    [Fact]
    public void Nested() =>
        Assert.Equal(0.5, Measurements.BrayCurtisGradient([1.0, 0.0, 0.0], [1.0, 1.0, 1.0]));

    [Fact]
    public void Huge() =>
        Assert.Equal(1.0 / 3.0, Measurements.BrayCurtisGradient([1.5e308, 0.0], [1.5e308, 1.5e308]), 15);

    [Fact]
    public void Disjoint() =>
        Assert.Equal(0.0, Measurements.BrayCurtisGradient([1.0, 0.0], [0.0, 1.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.BrayCurtisGradient([0.0, 0.0], [1.0, 2.0]));
}
