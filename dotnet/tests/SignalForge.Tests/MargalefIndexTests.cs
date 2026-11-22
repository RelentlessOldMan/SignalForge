using Xunit;

namespace SignalForge.Tests;

/// <summary>Margalef's index (ADR 0542).</summary>
public class MargalefIndexTests
{
    [Fact]
    public void OneZero() =>
        Assert.Equal(2.0 / Math.Log(6.0), Measurements.MargalefIndex([0.0, 2.0, 2.0, 2.0]), 14);

    [Fact]
    public void OneHoldsAll() =>
        Assert.Equal(0.0, Measurements.MargalefIndex([0.0, 4.0]), 15);

    [Fact]
    public void RejectsTotalOfOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.MargalefIndex([0.5, 0.5]));
}
