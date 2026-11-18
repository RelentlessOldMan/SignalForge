using Xunit;

namespace SignalForge.Tests;

/// <summary>Haas widener (ADR 0276).</summary>
public class HaasTests
{
    [Fact]
    public void LeftSideLate()
    {
        LeftRight y = Dsp.Haas([1.0, 2.0, 3.0], 1, StereoSide.Left);
        Assert.Equal([0.0, 1.0, 2.0], y.Left);
        Assert.Equal([1.0, 2.0, 3.0], y.Right);
    }

    [Fact]
    public void RejectsNegativeDelay() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Haas([1.0], -1));
}
