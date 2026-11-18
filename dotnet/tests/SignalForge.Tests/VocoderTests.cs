using Xunit;

namespace SignalForge.Tests;

/// <summary>Channel vocoder (ADR 0293).</summary>
public class VocoderTests
{
    [Fact]
    public void ASilentModulatorGivesSilence()
    {
        double[] c = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2];
        Assert.All(Dsp.Vocoder(c, new double[6], 4, 0.02, 0.4, 4.0, 0.5, 0.9, 1.0), v => Assert.Equal(0.0, v));
    }

    [Fact]
    public void RejectsMismatchedLengths() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Vocoder([1.0, 2.0], [1.0], 2, 0.5, 2.0, 2.0, 0.5, 0.5, 8.0));
}
