using Xunit;

namespace SignalForge.Tests;

/// <summary>Attention entropy (ADR 0346).</summary>
public class AttentionEntropyTests
{
    [Fact]
    public void AZigzagIsZero() =>
        Assert.Equal(0.0, Measurements.AttentionEntropy([0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0]), 1e-15);

    [Fact]
    public void TwoLengthsByHand()
    {
        // Maxima 1, 3, 6, 8; minima 2, 7. Max-max 2, 3, 2; min-min 5; max-min 1, 4, 1;
        // min-max 1, 1.
        double h = -((2.0 / 3 * Math.Log(2.0 / 3)) + (1.0 / 3 * Math.Log(1.0 / 3)));
        Assert.Equal(2 * h / 4, Measurements.AttentionEntropy([0.0, 2.0, 1.0, 3.0, 0.0, 0.0, 4.0, 1.0, 5.0, 0.0]), 1e-15);
    }

    [Fact]
    public void RejectsARamp() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.AttentionEntropy([0.0, 1.0, 2.0, 3.0]));
}
