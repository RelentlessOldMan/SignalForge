using Xunit;

namespace SignalForge.Tests;

/// <summary>The Lance-Williams distance (ADR 0476).</summary>
public class LanceWilliamsDistanceTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.2, Measurements.LanceWilliamsDistance([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsRecordsBothAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.LanceWilliamsDistance([0.0, 0.0], [0.0, 0.0]));
}
