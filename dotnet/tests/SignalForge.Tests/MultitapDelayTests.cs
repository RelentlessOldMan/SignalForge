using Xunit;

namespace SignalForge.Tests;

/// <summary>Multi-tap delay (ADR 0300).</summary>
public class MultitapDelayTests
{
    [Fact]
    public void AnImpulseShowsEachTap()
    {
        double[] x = [1, 0, 0, 0, 0, 0];
        Assert.Equal([1, 0, 0.5, 0, -0.25, 0], Dsp.MultitapDelay(x, [2, 4], [0.5, -0.25]));
    }

    [Fact]
    public void RejectsMismatchedGains() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.MultitapDelay([1.0], [1, 2], [0.5]));
}
