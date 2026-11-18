using Xunit;

namespace SignalForge.Tests;

/// <summary>Sidechain compressor (ADR 0278).</summary>
public class DuckTests
{
    [Fact]
    public void SelfKeyedIsTheCompressor()
    {
        double[] x = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6];
        Assert.Equal(Dsp.Compress(x, -6.0, 4.0, 0.25, 0.75, 6.0, 2.0), Dsp.Duck(x, x, -6.0, 4.0, 0.25, 0.75, 6.0, 2.0));
    }

    [Fact]
    public void RejectsMismatchedKey() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Duck([1.0, 2.0], [1.0], 0.0, 2.0, 0.5, 0.5));
}
