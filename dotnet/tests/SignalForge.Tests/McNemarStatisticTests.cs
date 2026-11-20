using Xunit;

namespace SignalForge.Tests;

/// <summary>McNemar's statistic (ADR 0479).</summary>
public class McNemarStatisticTests
{
    [Fact]
    public void Lopsided() =>
        Assert.Equal(1.8, Measurements.McNemarStatistic([1, 1, 1, 1, 1, 0, 0], [0, 0, 0, 0, 1, 1, 0]), 15);

    [Fact]
    public void RejectsRecordsThatAgreeEverywhere() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.McNemarStatistic([1.0, 0.0], [1.0, 0.0]));
}
