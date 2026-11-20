using Xunit;

namespace SignalForge.Tests;

/// <summary>The size difference (ADR 0472).</summary>
public class SizeDifferenceTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.04, Measurements.SizeDifference([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsUnequalLengths() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.SizeDifference([0.0, 1.0], [1.0]));
}
