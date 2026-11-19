using Xunit;

namespace SignalForge.Tests;

/// <summary>The Canberra distance (ADR 0417).</summary>
public class CanberraDistanceTests
{
    [Fact]
    public void Mixed() =>
        Assert.Equal(5.0 / 6.0, Measurements.CanberraDistance([1.0, 3.0], [2.0, 1.0]), 1e-15);

    [Fact]
    public void RejectsUnequalLengths() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.CanberraDistance([1.0], [1.0, 1.0]));
}
