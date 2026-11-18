using Xunit;

namespace SignalForge.Tests;

/// <summary>Peak normalization (ADR 0268).</summary>
public class NormalizePeakTests
{
    [Fact]
    public void ScalesToPeak()
    {
        double[] y = Dsp.NormalizePeak([0.5, -0.25], 2.0);
        Assert.Equal([2.0, -1.0], y);
    }

    [Fact]
    public void RejectsSilence() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.NormalizePeak([0.0, 0.0]));
}
