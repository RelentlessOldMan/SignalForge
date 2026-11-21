using Xunit;

namespace SignalForge.Tests;

/// <summary>The Kwoka dominance index (ADR 0526).</summary>
public class KwokaDominanceIndexTests
{
    [Fact]
    public void Three() =>
        Assert.Equal(5.0 / 16.0, Measurements.KwokaDominanceIndex([3.0, 0.0, 1.0]), 15);

    [Fact]
    public void Halves() =>
        Assert.Equal(5.0 / 64.0, Measurements.KwokaDominanceIndex([0.5, 0.25, 0.25, 1.0]), 15);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.KwokaDominanceIndex([0.0, 0.0]));
}
