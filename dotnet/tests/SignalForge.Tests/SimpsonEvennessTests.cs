using Xunit;

namespace SignalForge.Tests;

/// <summary>Simpson's evenness (ADR 0532).</summary>
public class SimpsonEvennessTests
{
    [Fact]
    public void Halves() =>
        Assert.Equal(8.0 / 11.0, Measurements.SimpsonEvenness([0.5, 0.25, 0.25, 1.0]), 15);

    [Fact]
    public void Three() =>
        Assert.Equal(8.0 / 15.0, Measurements.SimpsonEvenness([3.0, 0.0, 1.0]), 15);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.SimpsonEvenness([0.0, 0.0]));
}
