using Xunit;

namespace SignalForge.Tests;

/// <summary>Bass enhancer (ADR 0290).</summary>
public class BassEnhancerTests
{
    [Fact]
    public void MixZeroIsTheInput()
    {
        double[] x = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6];
        Assert.Equal(x, Dsp.BassEnhancer(x, 4, 0.1, 1.0, 3.0, 0.0));
    }

    [Fact]
    public void RejectsZeroDrive() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.BassEnhancer([1.0], 4, 1.0, 8.0, 0.0, 0.5));
}
