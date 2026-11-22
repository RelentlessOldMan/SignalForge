using Xunit;

namespace SignalForge.Tests;

/// <summary>Simpson's beta of two records (ADR 0576).</summary>
public class SimpsonBetaTests
{
    [Fact]
    public void Nested() =>
        Assert.Equal(0.0, Measurements.SimpsonBeta([1.0, 0.0, 0.0], [1.0, 1.0, 1.0]));

    [Fact]
    public void Swap() =>
        Assert.Equal(2.0 / 3.0, Measurements.SimpsonBeta([1.0, 1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 0.0, 1.0, 1.0]), 15);

    [Fact]
    public void Disjoint() =>
        Assert.Equal(1.0, Measurements.SimpsonBeta([1.0, 0.0], [0.0, 1.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.SimpsonBeta([0.0, 0.0], [1.0, 2.0]));
}
