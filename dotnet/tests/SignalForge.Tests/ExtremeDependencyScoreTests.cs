using Xunit;

namespace SignalForge.Tests;

/// <summary>The extreme dependency score (ADR 0489).</summary>
public class ExtremeDependencyScoreTests
{
    [Fact]
    public void Square() =>
        Assert.Equal((2.0 * Math.Log(0.5) / Math.Log(0.4)) - 1.0, Measurements.ExtremeDependencyScore([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 14);

    [Fact]
    public void RejectsRecordsWithNoSharedOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ExtremeDependencyScore([1.0, 0.0], [0.0, 1.0]));
}
