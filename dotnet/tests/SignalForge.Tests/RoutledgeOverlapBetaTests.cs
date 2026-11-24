using Xunit;

namespace SignalForge.Tests;

/// <summary>Routledge's overlap beta of two presence records (ADR 0597).</summary>
public class RoutledgeOverlapBetaTests
{
    [Fact]
    public void Nested() =>
        Assert.Equal(0.0, Measurements.RoutledgeOverlapBeta([1.0, 0.0, 0.0], [1.0, 1.0, 1.0]));

    [Fact]
    public void Uneven() =>
        Assert.Equal(2.0 / 7.0, Measurements.RoutledgeOverlapBeta([1.0, 1.0, 0.0, 1.0, 1.0, 1.0], [1.0, 0.0, 1.0, 0.0, 0.0, 0.0]), 15);

    [Fact]
    public void Disjoint() =>
        Assert.Equal(1.0, Measurements.RoutledgeOverlapBeta([1.0, 0.0], [0.0, 1.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.RoutledgeOverlapBeta([0.0, 0.0], [1.0, 2.0]));
}
