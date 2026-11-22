using Xunit;

namespace SignalForge.Tests;

/// <summary>Horn's information overlap (ADR 0574).</summary>
public class HornOverlapTests
{
    [Fact]
    public void Swapped() =>
        Assert.Equal(2.0 - 0.75 * Math.Log2(3.0), Measurements.HornOverlap([1.0, 3.0], [3.0, 1.0]), 14);

    [Fact]
    public void HugeValues() =>
        Assert.Equal(6 * Math.Log(2) / (7 * Math.Log(7) - 3 * Math.Log(3) - 8 * Math.Log(2)), Measurements.HornOverlap([1e300, 2e300], [3e300, 1e300]), 14);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HornOverlap([0.0, 0.0], [1.0, 2.0]));
}
