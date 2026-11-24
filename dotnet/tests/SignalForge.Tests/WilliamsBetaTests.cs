using Xunit;

namespace SignalForge.Tests;

/// <summary>Williams' beta of two presence records (ADR 0593).</summary>
public class WilliamsBetaTests
{
    [Fact]
    public void Nested() =>
        Assert.Equal(0.0, Measurements.WilliamsBeta([1.0, 0.0, 0.0], [1.0, 1.0, 1.0]));

    [Fact]
    public void Uneven() =>
        Assert.Equal(1.0 / 6.0, Measurements.WilliamsBeta([1.0, 1.0, 0.0, 1.0, 1.0, 1.0], [1.0, 0.0, 1.0, 0.0, 0.0, 0.0]), 15);

    [Fact]
    public void Disjoint() =>
        Assert.Equal(0.5, Measurements.WilliamsBeta([1.0, 0.0], [0.0, 1.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.WilliamsBeta([0.0, 0.0], [1.0, 2.0]));
}
