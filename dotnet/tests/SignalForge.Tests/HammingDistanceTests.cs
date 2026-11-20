using Xunit;

namespace SignalForge.Tests;

/// <summary>The Hamming distance (ADR 0421).</summary>
public class HammingDistanceTests
{
    [Fact]
    public void SignedZerosAreEqual() =>
        Assert.Equal(1, Measurements.HammingDistance([0.0, 1.0, 2.0], [-0.0, 1.0, 5.0]));

    [Fact]
    public void RejectsNaN() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HammingDistance([double.NaN], [double.NaN]));
}
