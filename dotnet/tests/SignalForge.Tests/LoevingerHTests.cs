using Xunit;

namespace SignalForge.Tests;

/// <summary>Loevinger's H (ADR 0441).</summary>
public class LoevingerHTests
{
    [Fact]
    public void FarBelow() =>
        Assert.Equal(-3.0, Measurements.LoevingerH([1, 0, 0, 0], [0, 1, 1, 1]), 15);

    [Fact]
    public void RejectsAConstantRecord() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.LoevingerH([1.0, 1.0], [1.0, 0.0]));
}
