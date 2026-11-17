using Xunit;

namespace SignalForge.Tests;

/// <summary>Dead zone (ADR 0246).</summary>
public class DeadZoneTests
{
    [Fact]
    public void ZeroInsideShiftedOutside()
    {
        double[] y = Dsp.DeadZone([-3.0, -1.0, 0.5, 1.0, 2.5], 1.0);
        double[] want = [-2.0, 0.0, 0.0, 0.0, 1.5];
        Assert.Equal(want, y);
    }

    [Fact]
    public void RejectsNegativeWidth() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.DeadZone([1.0], -1.0));
}
