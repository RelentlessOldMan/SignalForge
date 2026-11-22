using Xunit;

namespace SignalForge.Tests;

/// <summary>The proportional similarity (ADR 0572).</summary>
public class CzekanowskiSimilarityTests
{
    [Fact]
    public void Reversed() =>
        Assert.Equal(2.0 / 3.0, Measurements.CzekanowskiSimilarity([1.0, 2.0, 3.0], [3.0, 2.0, 1.0]), 14);

    [Fact]
    public void HugeValues() =>
        Assert.Equal(11.0 / 12.0, Measurements.CzekanowskiSimilarity([1e300, 2e300], [1.0, 3.0]), 14);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.CzekanowskiSimilarity([0.0, 0.0], [1.0, 2.0]));
}
