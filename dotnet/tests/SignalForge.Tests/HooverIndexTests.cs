using Xunit;

namespace SignalForge.Tests;

/// <summary>The Hoover index (ADR 0512).</summary>
public class HooverIndexTests
{
    [Fact]
    public void Ramp() =>
        Assert.Equal(0.2, Measurements.HooverIndex([4.0, 1.0, 3.0, 2.0]), 15);

    [Fact]
    public void OneHoldsAll() =>
        Assert.Equal(0.75, Measurements.HooverIndex([0.0, 4.0, 0.0, 0.0]), 15);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HooverIndex([0.0, 0.0]));

    [Fact]
    public void RejectsANegativeValue() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HooverIndex([1.0, -1.0]));
}
