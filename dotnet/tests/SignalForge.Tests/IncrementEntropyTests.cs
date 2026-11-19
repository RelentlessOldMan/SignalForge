using Xunit;

namespace SignalForge.Tests;

/// <summary>Increment entropy (ADR 0344).</summary>
public class IncrementEntropyTests
{
    [Fact]
    public void ZigzagByHand()
    {
        // Steps +1, −1, …: two words, alternating, 3 and 2 times.
        double expected = -((0.6 * Math.Log(0.6)) + (0.4 * Math.Log(0.4)));
        Assert.Equal(expected, Measurements.IncrementEntropy([0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0], 2, 3), 1e-15);
    }

    [Fact]
    public void OneRepeatedWordIsZero() =>
        Assert.Equal(0.0, Measurements.IncrementEntropy([0.0, 1.0, 0.0, 1.0, 0.0], 4, 2), 1e-15);

    [Fact]
    public void RejectsARamp() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.IncrementEntropy([0.0, 1.0, 2.0, 3.0], 1, 2));
}
