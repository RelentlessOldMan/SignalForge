using Xunit;

namespace SignalForge.Tests;

/// <summary>Pianka's niche overlap (ADR 0571).</summary>
public class PiankaOverlapTests
{
    [Fact]
    public void Reversed() =>
        Assert.Equal(5.0 / 7.0, Measurements.PiankaOverlap([1.0, 2.0, 3.0], [3.0, 2.0, 1.0]), 14);

    [Fact]
    public void HugeValues() =>
        Assert.Equal(7.0 / Math.Sqrt(50.0), Measurements.PiankaOverlap([1e300, 2e300], [1.0, 3.0]), 14);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.PiankaOverlap([0.0, 0.0], [1.0, 2.0]));
}
