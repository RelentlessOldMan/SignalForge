using Xunit;

namespace SignalForge.Tests;

/// <summary>Noise gate (ADR 0255).</summary>
public class NoiseGateTests
{
    [Fact]
    public void HoldKeepsTheGateOpen()
    {
        double[] y = Dsp.NoiseGate([2.0, 0.5, 0.25, 0.125, 0.5], 1.0, 2);
        double[] want = [2.0, 0.5, 0.25, 0.0, 0.0];
        Assert.Equal(want, y);
    }

    [Fact]
    public void RejectsNegativeHold() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.NoiseGate([1.0], 0.5, -1));
}
