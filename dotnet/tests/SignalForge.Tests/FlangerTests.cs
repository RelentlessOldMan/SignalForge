using Xunit;

namespace SignalForge.Tests;

/// <summary>Flanger (ADR 0272).</summary>
public class FlangerTests
{
    [Fact]
    public void FixedDelayAtHalfMix()
    {
        double[] y = Dsp.Flanger([2.0, 4.0, -2.0], 1.0, 0.0, 1.0, 8.0, 0.5);
        Assert.Equal([1.0, 3.0, 1.0], y);
    }

    [Fact]
    public void RejectsMixAboveOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Flanger([1.0], 1.0, 0.5, 1.0, 8.0, 2.0));
}
