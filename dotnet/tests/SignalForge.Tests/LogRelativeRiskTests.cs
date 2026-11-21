using Xunit;

namespace SignalForge.Tests;

/// <summary>The log relative risk (ADR 0509).</summary>
public class LogRelativeRiskTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(Math.Log(4.0), Measurements.LogRelativeRisk([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsNoFalseNegative() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.LogRelativeRisk([1.0, 0.0, 1.0, 0.0], [1.0, 1.0, 1.0, 0.0]));
}
