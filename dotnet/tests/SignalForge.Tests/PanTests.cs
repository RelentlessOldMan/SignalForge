using Xunit;

namespace SignalForge.Tests;

/// <summary>Panner (ADR 0265).</summary>
public class PanTests
{
    [Fact]
    public void LinearHalvesAtCentre()
    {
        LeftRight lr = Dsp.Pan([2.0, -1.0], 0.0, PanLaw.Linear);
        Assert.Equal([1.0, -0.5], lr.Left);
        Assert.Equal([1.0, -0.5], lr.Right);
    }

    [Fact]
    public void RejectsPositionOutOfRange() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Pan([1.0], 2.0));
}
