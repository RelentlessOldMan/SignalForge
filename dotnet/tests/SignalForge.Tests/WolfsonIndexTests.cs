using Xunit;

namespace SignalForge.Tests;

/// <summary>The Wolfson polarization index (ADR 0522).</summary>
public class WolfsonIndexTests
{
    [Fact]
    public void Three() =>
        Assert.Equal(2.0 / 3.0, Measurements.WolfsonIndex([3.0, 0.0, 1.0]), 14);

    [Fact]
    public void Halves() =>
        Assert.Equal(0.5, Measurements.WolfsonIndex([0.5, 0.25, 0.25, 1.0]), 14);

    [Fact]
    public void RejectsAZeroMedian() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.WolfsonIndex([0.0, 0.0, 0.0, 1.0, 2.0]));
}
