using Xunit;

namespace SignalForge.Tests;

/// <summary>Bubble entropy (ADR 0345).</summary>
public class BubbleEntropyTests
{
    [Fact]
    public void AlternatingByHand()
    {
        // m = 2: 9 windows, 5 with 0 swaps and 4 with 1: Σp² = 41/81. m = 3: all one swap.
        double[] x = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0];
        Assert.Equal(Math.Log(41.0 / 81) / Math.Log(3), Measurements.BubbleEntropy(x, 2), 1e-15);
    }

    [Fact]
    public void ARampIsZero() =>
        Assert.Equal(0.0, Measurements.BubbleEntropy([0.0, 1.0, 2.0, 3.0, 4.0], 3), 1e-15);

    [Fact]
    public void RejectsTooShort() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.BubbleEntropy([0.0, 1.0, 2.0], 3));
}
