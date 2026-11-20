using Xunit;

namespace SignalForge.Tests;

/// <summary>The chord distance of two binary records (ADR 0477).</summary>
public class ChordDistanceTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(Math.Sqrt(0.4), Measurements.ChordDistance([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 14);

    [Fact]
    public void RejectsARecordWithNoOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ChordDistance([0.0, 0.0], [1.0, 0.0]));
}
