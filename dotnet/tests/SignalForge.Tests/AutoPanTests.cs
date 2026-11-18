using Xunit;

namespace SignalForge.Tests;

/// <summary>Auto-panner (ADR 0270).</summary>
public class AutoPanTests
{
    [Fact]
    public void StartsAtDepth()
    {
        LeftRight lr = Dsp.AutoPan([1.0, 1.0], 1.0, 0.5, 8.0, PanLaw.Linear);
        Assert.Equal(0.25, lr.Left[0]);
        Assert.Equal(0.75, lr.Right[0]);
    }

    [Fact]
    public void RejectsDepthAboveOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.AutoPan([1.0], 1.0, 1.5, 8.0));
}
