using Xunit;

namespace SignalForge.Tests;

/// <summary>Lloyd's mean crowding (ADR 0609).</summary>
public class LloydMeanCrowdingTests
{
    [Fact]
    public void Mixed() =>
        Assert.Equal(4.0 / 3.0, Measurements.LloydMeanCrowding([1.0, 2.0, 3.0]), 14);

    [Fact]
    public void Singles() =>
        Assert.Equal(0.0, Measurements.LloydMeanCrowding([1.0, 1.0, 0.0]));

    [Fact]
    public void Clumped() =>
        Assert.Equal(5.0, Measurements.LloydMeanCrowding([0.0, 0.0, 6.0]), 15);

    [Fact]
    public void RejectsFraction() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.LloydMeanCrowding([1.5, 2.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.LloydMeanCrowding([0.0, 0.0]));
}
