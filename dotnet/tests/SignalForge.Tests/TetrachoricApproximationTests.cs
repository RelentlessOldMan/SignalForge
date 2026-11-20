using Xunit;

namespace SignalForge.Tests;

/// <summary>The tetrachoric approximation (ADR 0492).</summary>
public class TetrachoricApproximationTests
{
    [Fact]
    public void Square() =>
        Assert.Equal((1.0 + Math.Sqrt(5.0)) / 4.0, Measurements.TetrachoricApproximation([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 14);

    [Fact]
    public void RejectsRecordsThatDisagreeOneWayOnly() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.TetrachoricApproximation([1.0, 0.0, 1.0, 0.0], [1.0, 1.0, 1.0, 0.0]));
}
