using Xunit;

namespace SignalForge.Tests;

/// <summary>The McIntosh evenness (ADR 0540).</summary>
public class McIntoshEvennessTests
{
    [Fact]
    public void OneZero() =>
        Assert.Equal((6.0 - (2.0 * Math.Sqrt(3.0))) / 3.0,
            Measurements.McIntoshEvenness([0.0, 2.0, 2.0, 2.0]), 14);

    [Fact]
    public void Equal() =>
        Assert.Equal(1.0, Measurements.McIntoshEvenness([0.5, 0.5, 0.5]), 13);

    [Fact]
    public void RejectsOneValue() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.McIntoshEvenness([5.0]));
}
