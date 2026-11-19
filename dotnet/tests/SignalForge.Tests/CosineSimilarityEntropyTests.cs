using Xunit;

namespace SignalForge.Tests;

/// <summary>Cosine similarity entropy (ADR 0358).</summary>
public class CosineSimilarityEntropyTests
{
    [Fact]
    public void SignsByHand() =>
        Assert.Equal(1.0, Measurements.CosineSimilarityEntropy([1.0, 2.0, -1.0, 3.0], 1, 0.5));

    [Fact]
    public void OneSimilarPairOfThree() =>
        Assert.Equal(Math.Log2(3) - 2.0 / 3, Measurements.CosineSimilarityEntropy([1.0, 0.0, 1.0, 0.0], 2, 0.4), 1e-15);

    [Fact]
    public void RejectsAZeroVector() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.CosineSimilarityEntropy([1.0, 0.0, 0.0, 2.0], 2, 0.5));
}
