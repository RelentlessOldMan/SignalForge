using Xunit;

namespace SignalForge.Tests;

/// <summary>The Tsallis diversity of counts (ADR 0568).</summary>
public class TsallisDiversityTests
{
    [Fact]
    public void Simpson() =>
        Assert.Equal(5.0 / 8.0, Measurements.TsallisDiversity([1.0, 1.0, 2.0], 2.0), 14);

    [Fact]
    public void Shannon() =>
        Assert.Equal(Math.Log(2.0), Measurements.TsallisDiversity([1.0, 1.0], 1.0), 14);

    [Fact]
    public void RejectsNegativeOrder() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.TsallisDiversity([1.0], -0.5));
}
