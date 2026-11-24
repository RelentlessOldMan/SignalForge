using Xunit;

namespace SignalForge.Tests;

/// <summary>Lennon's gradient beta of two presence records (ADR 0594).</summary>
public class LennonGradientBetaTests
{
    [Fact]
    public void Nested() =>
        Assert.Equal(1.0, Measurements.LennonGradientBeta([1.0, 0.0, 0.0], [1.0, 1.0, 1.0]));

    [Fact]
    public void Uneven() =>
        Assert.Equal(6.0 / 7.0, Measurements.LennonGradientBeta([1.0, 1.0, 0.0, 1.0, 1.0, 1.0], [1.0, 0.0, 1.0, 0.0, 0.0, 0.0]), 15);

    [Fact]
    public void Disjoint() =>
        Assert.Equal(0.0, Measurements.LennonGradientBeta([1.0, 0.0], [0.0, 1.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.LennonGradientBeta([0.0, 0.0], [1.0, 2.0]));
}
