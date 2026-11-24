using Xunit;

namespace SignalForge.Tests;

/// <summary>Harrison's beta of two presence records (ADR 0589).</summary>
public class HarrisonBetaTests
{
    [Fact]
    public void Nested() =>
        Assert.Equal(0.0, Measurements.HarrisonBeta([1.0, 0.0, 0.0], [1.0, 1.0, 1.0]));

    [Fact]
    public void Uneven() =>
        Assert.Equal(0.2, Measurements.HarrisonBeta([1.0, 1.0, 0.0, 1.0, 1.0, 1.0], [1.0, 0.0, 1.0, 0.0, 0.0, 0.0]), 15);

    [Fact]
    public void Disjoint() =>
        Assert.Equal(1.0, Measurements.HarrisonBeta([1.0, 0.0], [0.0, 1.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HarrisonBeta([0.0, 0.0], [1.0, 2.0]));
}
