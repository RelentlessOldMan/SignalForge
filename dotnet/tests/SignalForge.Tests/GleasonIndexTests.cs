using Xunit;

namespace SignalForge.Tests;

/// <summary>Gleason's index (ADR 0543).</summary>
public class GleasonIndexTests
{
    [Fact]
    public void OneZero() =>
        Assert.Equal(3.0 / Math.Log(6.0), Measurements.GleasonIndex([0.0, 2.0, 2.0, 2.0]), 14);

    [Fact]
    public void Two() =>
        Assert.Equal(1.0 / Math.Log(2.0), Measurements.GleasonIndex([3.0, 1.0]), 14);

    [Fact]
    public void RejectsTotalOfOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.GleasonIndex([0.5, 0.5]));
}
