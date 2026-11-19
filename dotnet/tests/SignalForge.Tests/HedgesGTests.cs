using Xunit;

namespace SignalForge.Tests;

/// <summary>Hedges' g (ADR 0398).</summary>
public class HedgesGTests
{
    [Fact]
    public void Two() =>
        Assert.Equal(4 / Math.Sqrt(2 * Math.PI), Measurements.HedgesG([4.0, 6.0, 8.0], [0.0, 2.0, 4.0]), 1e-14);

    [Fact]
    public void RejectsNoSpread() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HedgesG([1.0, 1.0], [2.0, 2.0]));
}
