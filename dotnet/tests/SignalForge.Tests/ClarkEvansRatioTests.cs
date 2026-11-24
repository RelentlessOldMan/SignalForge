using Xunit;

namespace SignalForge.Tests;

/// <summary>The Clark-Evans aggregation index (ADR 0616).</summary>
public class ClarkEvansRatioTests
{
    [Fact]
    public void RandomMean() =>
        Assert.Equal(1.0, Measurements.ClarkEvansRatio([0.5, 0.5], 1.0), 15);

    [Fact]
    public void Clumped() =>
        Assert.Equal(1.5, Measurements.ClarkEvansRatio([0.25, 0.25, 0.625], 4.0), 14);

    [Fact]
    public void Coincident() =>
        Assert.Equal(0.0, Measurements.ClarkEvansRatio([0.0, 0.0], 3.0));

    [Fact]
    public void RejectsZeroDensity() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ClarkEvansRatio([1.0], 0.0));

    [Fact]
    public void RejectsOverflow() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ClarkEvansRatio([1e308], 4.0));
}
