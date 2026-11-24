using Xunit;

namespace SignalForge.Tests;

/// <summary>Cody's beta of two presence records (ADR 0590).</summary>
public class CodyBetaTests
{
    [Fact]
    public void Nested() =>
        Assert.Equal(1.0, Measurements.CodyBeta([1.0, 0.0, 0.0], [1.0, 1.0, 1.0]));

    [Fact]
    public void Uneven() =>
        Assert.Equal(2.5, Measurements.CodyBeta([1.0, 1.0, 0.0, 1.0, 1.0, 1.0], [1.0, 0.0, 1.0, 0.0, 0.0, 0.0]));

    [Fact]
    public void Disjoint() =>
        Assert.Equal(1.0, Measurements.CodyBeta([1.0, 0.0], [0.0, 1.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.CodyBeta([0.0, 0.0], [1.0, 2.0]));
}
