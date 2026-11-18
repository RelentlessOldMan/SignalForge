using Xunit;

namespace SignalForge.Tests;

/// <summary>Two-operator FM tone (ADR 0306).</summary>
public class FmToneTests
{
    [Fact]
    public void ZeroIndexIsTheCarrier()
    {
        double[] y = Waveforms.FmTone(8000, 16, 1000, 300, 0.0, 0.5);
        double[] want = Waveforms.RealTone(8000, 16, 1000, 0.5);
        for (int n = 0; n < y.Length; n++)
            Assert.Equal(want[n], y[n], 1e-15);
    }

    [Fact]
    public void RejectsZeroSampleRate() =>
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.FmTone(0, 4, 1000, 250, 1));
}
