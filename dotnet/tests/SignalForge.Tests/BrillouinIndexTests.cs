using Xunit;

namespace SignalForge.Tests;

/// <summary>The Brillouin index (ADR 0546).</summary>
public class BrillouinIndexTests
{
    [Fact]
    public void Ramp() =>
        Assert.Equal(Math.Log(60.0) / 6.0, Measurements.BrillouinIndex([1.0, 2.0, 3.0]), 14);

    [Fact]
    public void OneHoldsAll() =>
        Assert.Equal(0.0, Measurements.BrillouinIndex([0.0, 4.0]), 15);

    [Fact]
    public void RejectsFractions() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.BrillouinIndex([1.5, 2.0]));
}
