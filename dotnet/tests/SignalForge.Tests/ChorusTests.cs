using Xunit;

namespace SignalForge.Tests;

/// <summary>Chorus (ADR 0273).</summary>
public class ChorusTests
{
    [Fact]
    public void OneVoiceIsTheFlanger()
    {
        double[] x = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2];
        Assert.Equal(Dsp.Flanger(x, 2.5, 1.0, 1.25, 10.0, 0.3), Dsp.Chorus(x, 2.5, 1.0, 1.25, 10.0, 1, 0.3));
    }

    [Fact]
    public void RejectsZeroVoices() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Chorus([1.0], 2.0, 1.0, 1.0, 8.0, 0, 0.5));
}
