using Xunit;

namespace SignalForge.Tests;

/// <summary>Hurlbert's niche overlap (ADR 0600).</summary>
public class HurlbertOverlapTests
{
    [Fact]
    public void AsAvailable() =>
        Assert.Equal(1.0, Measurements.HurlbertOverlap([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], [1.0, 2.0, 3.0]), 15);

    [Fact]
    public void Uneven() =>
        Assert.Equal(1.125, Measurements.HurlbertOverlap([2.0, 1.0, 1.0], [1.0, 1.0, 2.0], [1.0, 2.0, 1.0]), 15);

    [Fact]
    public void Disjoint() =>
        Assert.Equal(0.0, Measurements.HurlbertOverlap([1.0, 0.0], [0.0, 1.0], [1.0, 1.0]));

    [Fact]
    public void RejectsUnavailableKind() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HurlbertOverlap([1.0, 1.0], [1.0, 1.0], [1.0, 0.0]));

    [Fact]
    public void RejectsOverflow() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HurlbertOverlap([1.0, 1.0, 1.0], [1.0, 1.0, 1.0], [1.0, 1e-310, 1.0]));
}
