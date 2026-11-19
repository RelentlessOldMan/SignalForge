using Xunit;

namespace SignalForge.Tests;

/// <summary>The Chebyshev distance (ADR 0420).</summary>
public class ChebyshevDistanceTests
{
    [Fact]
    public void Triangle() =>
        Assert.Equal(4.0, Measurements.ChebyshevDistance([0.0, 0.0], [3.0, 4.0]));

    [Fact]
    public void RejectsAnOverflowingDifference() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ChebyshevDistance([1e308], [-1e308]));
}
