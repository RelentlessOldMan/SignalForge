using Xunit;

namespace SignalForge.Tests;

/// <summary>The Berger-Parker index (ADR 0530).</summary>
public class BergerParkerIndexTests
{
    [Fact]
    public void Ramp() =>
        Assert.Equal(0.4, Measurements.BergerParkerIndex([4.0, 1.0, 3.0, 2.0]), 15);

    [Fact]
    public void Tie() =>
        Assert.Equal(0.375, Measurements.BergerParkerIndex([3.0, 3.0, 2.0]), 15);

    [Fact]
    public void RejectsANegativeValue() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.BergerParkerIndex([1.0, -1.0]));
}
