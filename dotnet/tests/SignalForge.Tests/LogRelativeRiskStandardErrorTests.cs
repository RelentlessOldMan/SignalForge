using Xunit;

namespace SignalForge.Tests;

/// <summary>The standard error of the log relative risk (ADR 0499).</summary>
public class LogRelativeRiskStandardErrorTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(Math.Sqrt(0.85), Measurements.LogRelativeRiskStandardError([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsATableWithNoTruePositive() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.LogRelativeRiskStandardError([1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 0.0, 1.0]));
}
