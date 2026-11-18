using Xunit;

namespace SignalForge.Tests;

/// <summary>Ping-pong delay (ADR 0275).</summary>
public class PingPongDelayTests
{
    [Fact]
    public void ImpulseBounces()
    {
        LeftRight y = Dsp.PingPongDelay([1.0, 0, 0, 0, 0, 0, 0], 2, 0.5, 1.0);
        Assert.Equal([0, 0, 1.0, 0, 0, 0, 0.25], y.Left);
        Assert.Equal([0, 0, 0, 0, 0.5, 0, 0], y.Right);
    }

    [Fact]
    public void RejectsUnitFeedback() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.PingPongDelay([1.0], 1, 1.0, 0.5));
}
