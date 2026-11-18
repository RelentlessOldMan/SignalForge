using Xunit;

namespace SignalForge.Tests;

/// <summary>Feed-forward compressor (ADR 0257).</summary>
public class CompressTests
{
    [Fact]
    public void InstantSquareRootAboveZeroDb()
    {
        double[] y = Dsp.Compress([0.5, 4.0, -100.0, 0.0], 0.0, 2.0, 0.0, 0.0);
        double[] want = [0.5, 2.0, -10.0, 0.0];
        for (int n = 0; n < want.Length; n++)
            Assert.Equal(want[n], y[n], 1e-12);
    }

    [Fact]
    public void RejectsInfiniteMakeup() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Compress([1.0], -10.0, 2.0, 0.5, 0.5, 0, double.PositiveInfinity));
}
