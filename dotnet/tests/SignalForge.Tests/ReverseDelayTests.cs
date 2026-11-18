using Xunit;

namespace SignalForge.Tests;

/// <summary>Reverse delay (ADR 0298).</summary>
public class ReverseDelayTests
{
    [Fact]
    public void PlaysThePreviousBlockBackwards()
    {
        double[] x = [1, 2, 3, 4, 5, 6, 7];
        Assert.Equal([0, 0, 0, 3, 2, 1, 6], Dsp.ReverseDelay(x, 3, 1.0));
    }

    [Fact]
    public void RejectsZeroBlock() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.ReverseDelay([1.0], 0, 0.5));
}
