using Xunit;

namespace SignalForge.Tests;

/// <summary>Hopkins' statistic (ADR 0618).</summary>
public class HopkinsStatisticTests
{
    [Fact]
    public void Equal() =>
        Assert.Equal(0.5, Measurements.HopkinsStatistic([1.0, 2.0], [2.0, 1.0]));

    [Fact]
    public void Clumped() =>
        Assert.Equal(25.0 / 26.0, Measurements.HopkinsStatistic([3.0, 4.0], [0.0, 0.0, 1.0]), 15);

    [Fact]
    public void Huge() =>
        Assert.Equal(2.0 / 3.0, Measurements.HopkinsStatistic([1e300, 1e300], [1e300]), 15);

    [Fact]
    public void RejectsEmpty() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HopkinsStatistic([], [1.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HopkinsStatistic([1.0], [0.0]));
}
