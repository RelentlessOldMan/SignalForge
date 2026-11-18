using Xunit;

namespace SignalForge.Tests;

/// <summary>Mid/side coding (ADR 0264).</summary>
public class MidSideTests
{
    [Fact]
    public void RoundTrip()
    {
        double[] left = [1.0, -0.5, 0.25], right = [0.5, 0.5, -2.0];
        MidSide ms = Dsp.MidSideEncode(left, right);
        LeftRight lr = Dsp.MidSideDecode(ms.Mid, ms.Side);
        Assert.Equal(left, lr.Left);
        Assert.Equal(right, lr.Right);
    }

    [Fact]
    public void RejectsUnequalLengths() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.MidSideEncode([1.0, 2.0], [1.0]));
}
