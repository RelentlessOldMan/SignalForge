using Xunit;

namespace SignalForge.Tests;

/// <summary>Pielou's evenness (ADR 0528).</summary>
public class PielouEvennessTests
{
    [Fact]
    public void Halves() =>
        Assert.Equal(0.875, Measurements.PielouEvenness([0.5, 0.25, 0.25, 1.0]), 14);

    [Fact]
    public void Equal() =>
        Assert.Equal(1.0, Measurements.PielouEvenness([2.0, 2.0, 2.0, 2.0]), 14);

    [Fact]
    public void RejectsOneValue() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.PielouEvenness([5.0]));
}
