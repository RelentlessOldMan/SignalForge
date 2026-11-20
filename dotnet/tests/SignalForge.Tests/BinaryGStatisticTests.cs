using Xunit;

namespace SignalForge.Tests;

/// <summary>The G statistic of two binary records (ADR 0481).</summary>
public class BinaryGStatisticTests
{
    [Fact]
    public void Identical() =>
        Assert.Equal(8 * Math.Log(2), Measurements.BinaryGStatistic([1, 0, 1, 0], [1, 0, 1, 0]), 13);

    [Fact]
    public void RejectsUnequalLengths() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.BinaryGStatistic([0.0, 1.0], [1.0]));
}
