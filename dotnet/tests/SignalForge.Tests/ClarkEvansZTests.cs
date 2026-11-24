using Xunit;

namespace SignalForge.Tests;

/// <summary>The Clark-Evans test statistic (ADR 0617).</summary>
public class ClarkEvansZTests
{
    [Fact]
    public void RandomMean() =>
        Assert.Equal(0.0, Measurements.ClarkEvansZ([0.5, 0.5], 1.0));

    [Fact]
    public void Quarter() =>
        Assert.Equal(Math.Sqrt(Math.PI / (4.0 - Math.PI)), Measurements.ClarkEvansZ([0.25], 16.0), 14);

    [Fact]
    public void Coincident() =>
        Assert.Equal(-Math.Sqrt(2.0 * Math.PI / (4.0 - Math.PI)), Measurements.ClarkEvansZ([0.0, 0.0], 3.0), 14);

    [Fact]
    public void RejectsZeroDensity() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ClarkEvansZ([1.0], 0.0));

    [Fact]
    public void RejectsOverflow() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ClarkEvansZ([1e308, 1e308], 0.25));
}
