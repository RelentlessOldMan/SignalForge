using Xunit;

namespace SignalForge.Tests;

/// <summary>Slicer (ADR 0294).</summary>
public class SlicerTests
{
    [Fact]
    public void OpensForTheDutyFraction()
    {
        double[] x = [1, 2, 3, 4, 5, 6, 7, 8, 9];
        Assert.Equal([1, 2, 3, 0, 0, 0, 0, 0, 9], Dsp.Slicer(x, 0.125, 0.375, 1.0));
    }

    [Fact]
    public void RejectsNegativeRate() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Slicer([1.0], -1.0, 0.5, 8.0));
}
