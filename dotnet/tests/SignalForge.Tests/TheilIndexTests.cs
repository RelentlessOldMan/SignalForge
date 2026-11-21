using Xunit;

namespace SignalForge.Tests;

/// <summary>The Theil index (ADR 0511).</summary>
public class TheilIndexTests
{
    [Fact]
    public void Halves() =>
        Assert.Equal(Math.Log(2.0), Measurements.TheilIndex([0.0, 2.0, 2.0, 0.0]), 15);

    [Fact]
    public void OneHoldsAll() =>
        Assert.Equal(Math.Log(4.0), Measurements.TheilIndex([0.0, 4.0, 0.0, 0.0]), 15);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.TheilIndex([0.0, 0.0]));

    [Fact]
    public void RejectsANegativeValue() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.TheilIndex([1.0, -1.0]));
}
