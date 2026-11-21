using Xunit;

namespace SignalForge.Tests;

/// <summary>The Hall-Tideman index (ADR 0525).</summary>
public class HallTidemanIndexTests
{
    [Fact]
    public void Ramp() =>
        Assert.Equal(1.0 / 3.0, Measurements.HallTidemanIndex([4.0, 1.0, 3.0, 2.0]), 15);

    [Fact]
    public void Halves() =>
        Assert.Equal(4.0 / 11.0, Measurements.HallTidemanIndex([0.5, 0.25, 0.25, 1.0]), 15);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HallTidemanIndex([0.0, 0.0]));
}
