using Xunit;

namespace SignalForge.Tests;

/// <summary>Digby's H (ADR 0444).</summary>
public class DigbyHTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(7.0 / 9.0, Measurements.DigbyH([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsATableWithBothProductsZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.DigbyH([1.0, 1.0, 1.0], [1.0, 0.0, 1.0]));
}
