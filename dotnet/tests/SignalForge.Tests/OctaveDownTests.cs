using Xunit;

namespace SignalForge.Tests;

/// <summary>Octave-down effect (ADR 0291).</summary>
public class OctaveDownTests
{
    [Fact]
    public void FlipsAtRisingCrossings()
    {
        double[] x = [-1.0, 0.0, 2.0, -3.0, 0.5];
        Assert.Equal([1.0, 0.0, -2.0, -3.0, 0.5], Dsp.OctaveDown(x, 1.0));
    }

    [Fact]
    public void RejectsEmptySamples() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.OctaveDown([], 0.5));
}
