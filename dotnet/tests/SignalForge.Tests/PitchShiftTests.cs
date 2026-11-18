using Xunit;

namespace SignalForge.Tests;

/// <summary>Delay-line pitch shifter (ADR 0302).</summary>
public class PitchShiftTests
{
    [Fact]
    public void UnityRatioDelaysByHalfAWindow()
    {
        double[] x = [1, 2, 3, 4, 5, 6];
        Assert.Equal([0, 0, 1, 2, 3, 4], Dsp.PitchShift(x, 1.0, 4.0));
    }

    [Fact]
    public void RejectsZeroRatio() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.PitchShift([1.0], 0.0, 8.0));
}
