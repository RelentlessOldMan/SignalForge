using Xunit;

namespace SignalForge.Tests;

/// <summary>Blomqvist's beta (ADR 0375).</summary>
public class BlomqvistBetaTests
{
    [Fact]
    public void EvenHand() =>
        Assert.Equal(0.0, Measurements.BlomqvistBeta([1.0, 2.0, 3.0, 4.0], [4.0, 1.0, 3.0, 2.0]));

    [Fact]
    public void Reversed() =>
        Assert.Equal(-1.0, Measurements.BlomqvistBeta([1.0, 2.0, 3.0], [3.0, 2.0, 1.0]));

    [Fact]
    public void RejectsEverySampleOnAMedian() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.BlomqvistBeta([1.0, 1.0, 1.0], [1.0, 2.0, 3.0]));
}
