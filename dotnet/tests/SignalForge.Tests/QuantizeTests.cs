using Xunit;

namespace SignalForge.Tests;

/// <summary>Uniform quantizer (ADR 0247).</summary>
public class QuantizeTests
{
    [Fact]
    public void TiesRoundToEvenAndSaturate()
    {
        double[] y = Dsp.Quantize([0.5, 1.5, 2.5, -2.5, 9.0], 1.0, 5);
        double[] want = [0.0, 2.0, 2.0, -2.0, 2.0];
        Assert.Equal(want, y);
    }

    [Fact]
    public void RejectsEvenLevels() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Quantize([1.0], 1.0, 4));
}
