using Xunit;

namespace SignalForge.Tests;

/// <summary>Eberhardt's index (ADR 0620).</summary>
public class EberhardtIndexTests
{
    [Fact]
    public void Three() =>
        Assert.Equal(7.0 / 6.0, Measurements.EberhardtIndex([1.0, 2.0, 3.0]), 14);

    [Fact]
    public void OneNonzero() =>
        Assert.Equal(3.0, Measurements.EberhardtIndex([0.0, 0.0, 4.0]));

    [Fact]
    public void Huge() =>
        Assert.Equal(1.25, Measurements.EberhardtIndex([1e300, 3e300]), 14);

    [Fact]
    public void RejectsEmpty() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.EberhardtIndex([]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.EberhardtIndex([0.0, 0.0]));
}
