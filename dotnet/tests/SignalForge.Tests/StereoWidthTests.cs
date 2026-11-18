using Xunit;

namespace SignalForge.Tests;

/// <summary>Stereo width (ADR 0267).</summary>
public class StereoWidthTests
{
    [Fact]
    public void ZeroWidthIsMono()
    {
        LeftRight lr = Dsp.StereoWidth([1.0, 2.0], [3.0, -2.0], 0.0);
        Assert.Equal([2.0, 0.0], lr.Left);
        Assert.Equal([2.0, 0.0], lr.Right);
    }

    [Fact]
    public void RejectsNegativeWidth() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.StereoWidth([1.0], [1.0], -1.0));
}
