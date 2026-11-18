using Xunit;

namespace SignalForge.Tests;

/// <summary>Weighted permutation entropy (ADR 0343).</summary>
public class WeightedPermutationEntropyTests
{
    [Fact]
    public void WeightsMatter()
    {
        // Rising windows weigh 1/4 + 25/4, the falling one 1/4.
        double p = 26.0 / 27, q = 1.0 / 27;
        double expected = -(p * Math.Log(p) + q * Math.Log(q)) / Math.Log(2);
        Assert.Equal(expected, Measurements.WeightedPermutationEntropy([0.0, 1.0, 0.0, 5.0], 2), 1e-15);
    }

    [Fact]
    public void ARampIsZero() =>
        Assert.Equal(0.0, Measurements.WeightedPermutationEntropy([0.0, 1.0, 2.0, 3.0, 4.0], 3), 1e-15);

    [Fact]
    public void RejectsAConstantRecord() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.WeightedPermutationEntropy([1.0, 1.0, 1.0, 1.0], 2));
}
