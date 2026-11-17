using Xunit;

namespace SignalForge.Tests;

/// <summary>Sample-and-hold (ADR 0245).</summary>
public class SampleAndHoldTests
{
    [Fact]
    public void HoldsEveryPeriodthSample()
    {
        double[] y = Dsp.SampleAndHold([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0], 3, 1);
        double[] want = [0.0, 2.0, 2.0, 2.0, 5.0, 5.0, 5.0];
        Assert.Equal(want, y);
    }

    [Fact]
    public void RejectsOffsetAtPeriod() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.SampleAndHold([1.0], 2, 2));
}
