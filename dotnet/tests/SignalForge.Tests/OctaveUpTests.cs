using Xunit;

namespace SignalForge.Tests;

/// <summary>Octave-up effect (ADR 0289).</summary>
public class OctaveUpTests
{
    [Fact]
    public void FullyWetIsTheBlockedRectifier()
    {
        double[] x = [0.3, -0.7, 1.1, 0.4, -0.9];
        double[] r = [.. x.Select(Math.Abs)];
        Assert.Equal(Dsp.DcBlocker(r, 0.9), Dsp.OctaveUp(x, 0.9, 1.0));
    }

    [Fact]
    public void RejectsNonFiniteSamples() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.OctaveUp([double.NaN], 0.5, 0.5));
}
