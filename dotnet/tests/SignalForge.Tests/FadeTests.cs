using Xunit;

namespace SignalForge.Tests;

/// <summary>Fades (ADR 0262).</summary>
public class FadeTests
{
    [Fact]
    public void LinearRamps()
    {
        double[] y = Dsp.Fade([1.0, 1.0, 1.0, 1.0, 1.0, 1.0], 4, 2);
        double[] want = [0.0, 0.25, 0.5, 0.75, 0.5, 0.0];
        Assert.Equal(want, y);
    }

    [Fact]
    public void RejectsFadeLongerThanSamples() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Fade([1.0], 2, 0));
}
