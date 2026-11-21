using Xunit;

namespace SignalForge.Tests;

/// <summary>The standard error of the Haldane log odds ratio (ADR 0497).</summary>
public class HaldaneLogOddsRatioStandardErrorTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(4.0 / 3.0, Measurements.HaldaneLogOddsRatioStandardError([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsRecordsOfDifferentLengths() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HaldaneLogOddsRatioStandardError([1.0, 0.0], [1.0]));
}
