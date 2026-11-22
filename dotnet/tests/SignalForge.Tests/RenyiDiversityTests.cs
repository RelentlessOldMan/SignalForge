using Xunit;

namespace SignalForge.Tests;

/// <summary>The Renyi diversity of counts (ADR 0566).</summary>
public class RenyiDiversityTests
{
    [Fact]
    public void InverseSimpson() =>
        Assert.Equal(Math.Log(8.0 / 3.0), Measurements.RenyiDiversity([1.0, 1.0, 2.0], 2.0), 14);

    [Fact]
    public void Shannon() =>
        Assert.Equal(1.5 * Math.Log(2.0), Measurements.RenyiDiversity([1.0, 1.0, 2.0], 1.0), 14);

    [Fact]
    public void RejectsNegativeOrder() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.RenyiDiversity([1.0], -1.0));
}
