using Xunit;

namespace SignalForge.Tests;

/// <summary>The Sharma-Mittal diversity of counts (ADR 0570).</summary>
public class SharmaMittalDiversityTests
{
    [Fact]
    public void Tsallis() =>
        Assert.Equal(5.0 / 8.0, Measurements.SharmaMittalDiversity([1.0, 1.0, 2.0], 2.0, 2.0), 14);

    [Fact]
    public void HillLessOne() =>
        Assert.Equal(5.0 / 3.0, Measurements.SharmaMittalDiversity([1.0, 1.0, 2.0], 2.0, 0.0), 14);

    [Fact]
    public void RejectsInfiniteDegree() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.SharmaMittalDiversity([1.0], 1.0, double.PositiveInfinity));
}
