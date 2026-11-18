using Xunit;

namespace SignalForge.Tests;

/// <summary>Tanh saturator (ADR 0259).</summary>
public class SaturateTests
{
    [Fact]
    public void UnityAtOne()
    {
        double[] y = Dsp.Saturate([-1.0, 0.0, 1.0], 2.0);
        Assert.Equal(-1.0, y[0], 1e-15);
        Assert.Equal(0.0, y[1]);
        Assert.Equal(1.0, y[2], 1e-15);
    }

    [Fact]
    public void RejectsZeroDrive() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Saturate([1.0], 0.0));
}
