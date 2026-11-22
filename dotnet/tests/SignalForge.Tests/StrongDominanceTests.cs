using Xunit;

namespace SignalForge.Tests;

/// <summary>Strong's dominance (ADR 0549).</summary>
public class StrongDominanceTests
{
    [Fact]
    public void Mixed() =>
        Assert.Equal(11.0 / 36.0, Measurements.StrongDominance([5.0, 1.0, 1.0, 0.0, 2.0]), 15);

    [Fact]
    public void Equal() =>
        Assert.Equal(0.0, Measurements.StrongDominance([2.0, 0.0, 2.0]), 15);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.StrongDominance([0.0, 0.0]));
}
