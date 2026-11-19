using Xunit;

namespace SignalForge.Tests;

/// <summary>Markedness (ADR 0395).</summary>
public class MarkednessTests
{
    [Fact]
    public void Hand() =>
        Assert.Equal(5.0 / 12, Measurements.Markedness([1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0]), 1e-15);

    [Fact]
    public void RejectsADecisionWithoutAZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.Markedness([1.0, 0.0], [1.0, 1.0]));
}
