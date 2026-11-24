using Xunit;

namespace SignalForge.Tests;

/// <summary>Wilson and Shmida's beta of two presence records (ADR 0591).</summary>
public class WilsonShmidaBetaTests
{
    [Fact]
    public void Nested() =>
        Assert.Equal(0.5, Measurements.WilsonShmidaBeta([1.0, 0.0, 0.0], [1.0, 1.0, 1.0]));

    [Fact]
    public void Uneven() =>
        Assert.Equal(5.0 / 7.0, Measurements.WilsonShmidaBeta([1.0, 1.0, 0.0, 1.0, 1.0, 1.0], [1.0, 0.0, 1.0, 0.0, 0.0, 0.0]), 15);

    [Fact]
    public void Disjoint() =>
        Assert.Equal(1.0, Measurements.WilsonShmidaBeta([1.0, 0.0], [0.0, 1.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.WilsonShmidaBeta([0.0, 0.0], [1.0, 2.0]));
}
