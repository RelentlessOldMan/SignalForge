using Xunit;

namespace SignalForge.Tests;

/// <summary>Cohen's d (ADR 0397).</summary>
public class CohenDTests
{
    [Fact]
    public void Two() =>
        Assert.Equal(2.0, Measurements.CohenD([4.0, 6.0, 8.0], [0.0, 2.0, 4.0]), 1e-15);

    [Fact]
    public void RejectsNoSpread() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.CohenD([1.0, 1.0], [2.0, 2.0]));
}
