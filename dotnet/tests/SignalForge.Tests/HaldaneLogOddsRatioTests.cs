using Xunit;

namespace SignalForge.Tests;

/// <summary>The Haldane log odds ratio (ADR 0494).</summary>
public class HaldaneLogOddsRatioTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(Math.Log(9.0), Measurements.HaldaneLogOddsRatio([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 14);

    [Fact]
    public void RejectsRecordsOfDifferentLengths() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HaldaneLogOddsRatio([1.0, 0.0], [1.0]));
}
