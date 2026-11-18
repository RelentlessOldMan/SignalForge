using Xunit;

namespace SignalForge.Tests;

/// <summary>Maximum time interval error (ADR 0337).</summary>
public class MtieTests
{
    [Fact]
    public void SpikeByHand()
    {
        Mtie m = Measurements.Mtie([0.0, 0.0, 5.0, 0.0, -1.0, 0.0], 0.5, [1, 2, 5]);
        Assert.Equal([0.5, 1.0, 2.5], m.Taus);
        Assert.Equal([5.0, 6.0, 6.0], m.Values);
    }

    [Fact]
    public void RejectsAZeroWindow() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.Mtie([0.0, 1.0, 2.0], 1, [0]));
}
