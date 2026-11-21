using Xunit;

namespace SignalForge.Tests;

/// <summary>Camargo's evenness (ADR 0533).</summary>
public class CamargoEvennessTests
{
    [Fact]
    public void Halves() =>
        Assert.Equal(11.0 / 16.0, Measurements.CamargoEvenness([0.5, 0.25, 0.25, 1.0]), 15);

    [Fact]
    public void Three() =>
        Assert.Equal(0.5, Measurements.CamargoEvenness([3.0, 0.0, 1.0]), 15);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.CamargoEvenness([0.0, 0.0]));
}
