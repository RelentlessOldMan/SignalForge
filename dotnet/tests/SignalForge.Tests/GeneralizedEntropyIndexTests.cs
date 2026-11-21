using Xunit;

namespace SignalForge.Tests;

/// <summary>The generalized entropy index (ADR 0516).</summary>
public class GeneralizedEntropyIndexTests
{
    [Fact]
    public void HalfCvSquared() =>
        Assert.Equal(0.125, Measurements.GeneralizedEntropyIndex([1.0, 3.0], 2.0), 15);

    [Fact]
    public void MinusOne() =>
        Assert.Equal(1.0 / 6.0, Measurements.GeneralizedEntropyIndex([3.0, 1.0], -1.0), 15);

    [Fact]
    public void RejectsAnInfiniteAlpha() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.GeneralizedEntropyIndex([1.0, 2.0], double.PositiveInfinity));
}
