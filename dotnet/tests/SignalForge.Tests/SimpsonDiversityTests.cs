using Xunit;

namespace SignalForge.Tests;

/// <summary>The Gini-Simpson index (ADR 0529).</summary>
public class SimpsonDiversityTests
{
    [Fact]
    public void Halves() =>
        Assert.Equal(21.0 / 32.0, Measurements.SimpsonDiversity([0.5, 0.25, 0.25, 1.0]), 15);

    [Fact]
    public void Ramp() =>
        Assert.Equal(0.7, Measurements.SimpsonDiversity([4.0, 1.0, 3.0, 2.0]), 15);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.SimpsonDiversity([0.0, 0.0]));
}
