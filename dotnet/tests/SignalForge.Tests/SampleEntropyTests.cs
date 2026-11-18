using Xunit;

namespace SignalForge.Tests;

/// <summary>Sample entropy (ADR 0326).</summary>
public class SampleEntropyTests
{
    [Fact]
    public void ByHand() =>
        Assert.Equal(Math.Log(3), Measurements.SampleEntropy([1.0, 2.0, 1.0, 3.0, 1.0, 2.0], 1, 0.5), 1e-15);

    [Fact]
    public void NoExtensionIsInfinite() =>
        Assert.Equal(double.PositiveInfinity, Measurements.SampleEntropy([0.0, 1.0, 0.0, 2.0, 0.0, 3.0], 1, 0.25));

    [Fact]
    public void RejectsNoMatchAtAll() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.SampleEntropy([0.0, 1.0, 2.0, 3.0], 1, 0.5));
}
