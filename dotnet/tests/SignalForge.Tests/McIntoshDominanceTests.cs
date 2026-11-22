using Xunit;

namespace SignalForge.Tests;

/// <summary>The McIntosh dominance (ADR 0539).</summary>
public class McIntoshDominanceTests
{
    [Fact]
    public void Two() =>
        Assert.Equal((4.0 - Math.Sqrt(10.0)) / 2.0, Measurements.McIntoshDominance([3.0, 1.0]), 14);

    [Fact]
    public void Ones() =>
        Assert.Equal(1.0, Measurements.McIntoshDominance([1.0, 1.0, 1.0, 1.0]), 14);

    [Fact]
    public void RejectsTotalOfOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.McIntoshDominance([0.5, 0.5]));
}
