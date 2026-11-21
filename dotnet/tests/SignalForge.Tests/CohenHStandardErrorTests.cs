using Xunit;

namespace SignalForge.Tests;

/// <summary>The standard error of Cohen's h (ADR 0507).</summary>
public class CohenHStandardErrorTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(Math.Sqrt(0.4), Measurements.CohenHStandardError([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsADecisionWithNoZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.CohenHStandardError([1.0, 0.0, 1.0], [1.0, 1.0, 1.0]));
}
