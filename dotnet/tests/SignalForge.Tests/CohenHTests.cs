using Xunit;

namespace SignalForge.Tests;

/// <summary>Cohen's h (ADR 0506).</summary>
public class CohenHTests
{
    [Fact]
    public void Quarter() =>
        Assert.Equal(-Math.PI / 6.0, Measurements.CohenH([1, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0]), 14);

    [Fact]
    public void RejectsADecisionWithNoZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.CohenH([1.0, 0.0, 1.0], [1.0, 1.0, 1.0]));
}
