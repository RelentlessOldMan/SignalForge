using Xunit;

namespace SignalForge.Tests;

/// <summary>Rectifier (ADR 0253).</summary>
public class RectifyTests
{
    [Fact]
    public void FullAndHalfWave()
    {
        double[] x = [-2.0, -0.5, 0.0, 1.5];
        double[] full = [2.0, 0.5, 0.0, 1.5];
        double[] half = [0.0, 0.0, 0.0, 1.5];
        Assert.Equal(full, Dsp.Rectify(x));
        Assert.Equal(half, Dsp.Rectify(x, full: false));
    }

    [Fact]
    public void RejectsEmpty() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Rectify([]));
}
