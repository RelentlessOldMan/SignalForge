using Xunit;

namespace SignalForge.Tests;

/// <summary>The Wald z of the log relative risk (ADR 0500).</summary>
public class LogRelativeRiskWaldZTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(Math.Log(4.0) * Math.Sqrt(20.0 / 17.0), Measurements.LogRelativeRiskWaldZ([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 14);

    [Fact]
    public void RejectsRecordsWhereEveryTruthIsOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.LogRelativeRiskWaldZ([1.0, 1.0, 1.0], [1.0, 0.0, 1.0]));
}
