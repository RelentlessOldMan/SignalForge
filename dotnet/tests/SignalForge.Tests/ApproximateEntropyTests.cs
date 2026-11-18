using Xunit;

namespace SignalForge.Tests;

/// <summary>Approximate entropy (ADR 0333).</summary>
public class ApproximateEntropyTests
{
    [Fact]
    public void AlternatingByHand()
    {
        // ±1, N = 6, r = 0.5: Φ1 = ln(1/2); Φ2 = (3 ln(3/5) + 2 ln(2/5))/5.
        double expected = Math.Log(0.5) - (((3 * Math.Log(0.6)) + (2 * Math.Log(0.4))) / 5);
        Assert.Equal(expected, Measurements.ApproximateEntropy([1.0, -1.0, 1.0, -1.0, 1.0, -1.0], 1, 0.5), 1e-15);
    }

    [Fact]
    public void ConstantIsZero() =>
        Assert.Equal(0.0, Measurements.ApproximateEntropy([2.0, 2.0, 2.0, 2.0, 2.0], 2, 0));

    [Fact]
    public void RejectsAShortRecord() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ApproximateEntropy([0.0, 1.0, 2.0], 2, 0.5));
}
