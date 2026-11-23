using Xunit;

namespace SignalForge.Tests;

/// <summary>The balanced-variation part of the Bray-Curtis dissimilarity (ADR 0582).</summary>
public class BrayCurtisBalancedTests
{
    [Fact]
    public void Nested() =>
        Assert.Equal(0.0, Measurements.BrayCurtisBalanced([1.0, 0.0, 0.0], [1.0, 1.0, 1.0]));

    [Fact]
    public void Huge() =>
        Assert.Equal(0.5, Measurements.BrayCurtisBalanced([1.5e308, 1.5e308, 0.0], [1.5e308, 0.0, 1.5e308]));

    [Fact]
    public void Disjoint() =>
        Assert.Equal(1.0, Measurements.BrayCurtisBalanced([1.0, 0.0], [0.0, 1.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.BrayCurtisBalanced([0.0, 0.0], [1.0, 2.0]));
}
