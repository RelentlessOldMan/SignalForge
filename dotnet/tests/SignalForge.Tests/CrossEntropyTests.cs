using Xunit;

namespace SignalForge.Tests;

/// <summary>The cross-entropy (ADR 0415).</summary>
public class CrossEntropyTests
{
    [Fact]
    public void FairCoin() =>
        Assert.Equal(Math.Log(2.0), Measurements.CrossEntropy([1.0, 1.0], [1.0, 1.0]), 1e-15);

    [Fact]
    public void RejectsAZeroQUnderAPositiveP() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.CrossEntropy([1.0, 1.0], [1.0, 0.0]));
}
