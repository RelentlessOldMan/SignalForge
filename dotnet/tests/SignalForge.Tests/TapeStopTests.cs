using Xunit;

namespace SignalForge.Tests;

/// <summary>Tape stop (ADR 0296).</summary>
public class TapeStopTests
{
    [Fact]
    public void ARampReadsBackItsPosition()
    {
        double[] x = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
        Assert.Equal([0, 1, 2, 2.75, 3.25, 3.5, 0, 0, 0, 0], Dsp.TapeStop(x, 2, 4));
    }

    [Fact]
    public void RejectsZeroLength() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.TapeStop([1.0], 0, 0));
}
