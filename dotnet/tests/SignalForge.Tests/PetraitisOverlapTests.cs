using Xunit;

namespace SignalForge.Tests;

/// <summary>Petraitis' specific overlap (ADR 0599).</summary>
public class PetraitisOverlapTests
{
    [Fact]
    public void Nested() =>
        Assert.Equal(1.0 / 3.0, Measurements.PetraitisOverlap([1.0, 0.0, 0.0], [1.0, 1.0, 1.0]), 15);

    [Fact]
    public void Uneven() =>
        Assert.Equal(0.0, Measurements.PetraitisOverlap([1.0, 1.0, 0.0, 1.0, 1.0, 1.0], [1.0, 0.0, 1.0, 0.0, 0.0, 0.0]));

    [Fact]
    public void Disjoint() =>
        Assert.Equal(0.0, Measurements.PetraitisOverlap([1.0, 0.0], [0.0, 1.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.PetraitisOverlap([0.0, 0.0], [1.0, 2.0]));
}
