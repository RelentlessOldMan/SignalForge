using Xunit;

namespace SignalForge.Tests;

/// <summary>Stutter (ADR 0299).</summary>
public class StutterTests
{
    [Fact]
    public void RepeatsTheSlice()
    {
        double[] x = [1, 2, 3, 4, 5, 6, 7, 8];
        Assert.Equal([1, 2, 3, 2, 3, 2, 3, 8], Dsp.Stutter(x, 1, 2, 3));
    }

    [Fact]
    public void RejectsNegativeRepeats() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Stutter([1.0], 0, 1, -1));
}
