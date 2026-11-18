using Xunit;

namespace SignalForge.Tests;

/// <summary>Permutation entropy (ADR 0325).</summary>
public class PermutationEntropyTests
{
    [Fact]
    public void ARampHasNoEntropy() =>
        Assert.Equal(0.0, Measurements.PermutationEntropy([1.0, 2.0, 3.0, 4.0], 3));

    [Fact]
    public void EqualRisesAndFallsGiveOne() =>
        Assert.Equal(1.0, Measurements.PermutationEntropy([0.0, 1.0, 0.0, 1.0, 0.0], 2), 1e-15);

    [Fact]
    public void TiesCountAsRising() =>
        Assert.Equal(0.0, Measurements.PermutationEntropy([2.0, 2.0, 2.0, 3.0], 2));

    [Fact]
    public void RejectsOrderNine() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.PermutationEntropy(new double[20], 9));
}
