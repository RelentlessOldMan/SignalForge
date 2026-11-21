using Xunit;

namespace SignalForge.Tests;

/// <summary>Heip's evenness (ADR 0531).</summary>
public class HeipEvennessTests
{
    [Fact]
    public void OneZero() =>
        Assert.Equal(0.75, Measurements.HeipEvenness([0.0, 2.0, 2.0, 2.0, 2.0]), 13);

    [Fact]
    public void Equal() =>
        Assert.Equal(1.0, Measurements.HeipEvenness([2.0, 2.0, 2.0, 2.0]), 13);

    [Fact]
    public void RejectsOneValue() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HeipEvenness([5.0]));
}
