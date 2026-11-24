using Xunit;

namespace SignalForge.Tests;

/// <summary>Routledge's exponential beta of two presence records (ADR 0596).</summary>
public class RoutledgeExponentialBetaTests
{
    [Fact]
    public void Nested() =>
        Assert.Equal(Math.Pow(2.0, 1.5) / Math.Pow(3.0, 0.75) - 1.0, Measurements.RoutledgeExponentialBeta([1.0, 0.0, 0.0], [1.0, 1.0, 1.0]), 14);

    [Fact]
    public void Uneven() =>
        Assert.Equal(7.0 / (Math.Pow(2.0, 4.0 / 7.0) * Math.Pow(5.0, 5.0 / 7.0)) - 1.0, Measurements.RoutledgeExponentialBeta([1.0, 1.0, 0.0, 1.0, 1.0, 1.0], [1.0, 0.0, 1.0, 0.0, 0.0, 0.0]), 14);

    [Fact]
    public void Disjoint() =>
        Assert.Equal(1.0, Measurements.RoutledgeExponentialBeta([1.0, 0.0], [0.0, 1.0]), 14);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.RoutledgeExponentialBeta([0.0, 0.0], [1.0, 2.0]));
}
