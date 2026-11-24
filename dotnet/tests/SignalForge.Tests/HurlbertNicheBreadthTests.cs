using Xunit;

namespace SignalForge.Tests;

/// <summary>Hurlbert's niche breadth (ADR 0601).</summary>
public class HurlbertNicheBreadthTests
{
    [Fact]
    public void EvenUse() =>
        Assert.Equal(0.75, Measurements.HurlbertNicheBreadth([1.0, 1.0], [1.0, 3.0]), 15);

    [Fact]
    public void UnevenStandardized() =>
        Assert.Equal(7.0 / 11.0, Measurements.HurlbertNicheBreadth([2.0, 1.0, 1.0], [1.0, 2.0, 1.0], standardized: true), 15);

    [Fact]
    public void ScarcestStandardized() =>
        Assert.Equal(0.0, Measurements.HurlbertNicheBreadth([1.0, 0.0], [1.0, 3.0], standardized: true));

    [Fact]
    public void RejectsOneKindStandardized() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HurlbertNicheBreadth([2.0], [5.0], standardized: true));

    [Fact]
    public void RejectsOverflow() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HurlbertNicheBreadth([1.0, 1.0, 1.0], [1.0, 1e-310, 1.0]));
}
