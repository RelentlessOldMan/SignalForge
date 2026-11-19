using Xunit;

namespace SignalForge.Tests;

/// <summary>The Bray–Curtis dissimilarity (ADR 0418).</summary>
public class BrayCurtisTests
{
    [Fact]
    public void Mixed() =>
        Assert.Equal(1.0 / 3.0, Measurements.BrayCurtis([3.0, 1.0], [1.0, 1.0]), 1e-15);

    [Fact]
    public void RejectsTwoZeroVectors() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.BrayCurtis([0.0, 0.0], [0.0, 0.0]));
}
