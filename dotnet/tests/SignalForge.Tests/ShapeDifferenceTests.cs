using Xunit;

namespace SignalForge.Tests;

/// <summary>The shape difference (ADR 0473).</summary>
public class ShapeDifferenceTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.2, Measurements.ShapeDifference([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsUnequalLengths() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ShapeDifference([0.0, 1.0], [1.0]));
}
