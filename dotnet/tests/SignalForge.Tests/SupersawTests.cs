using Xunit;

namespace SignalForge.Tests;

/// <summary>Supersaw (ADR 0316).</summary>
public class SupersawTests
{
    [Fact]
    public void OneVoiceIsThePolyblepSawtooth()
    {
        double[] expected = Waveforms.PolyblepSawtooth(8000, 100, 321, 0.7);
        double[] y = Waveforms.Supersaw(8000, 100, 321, 40, 1, 0.7);
        for (int n = 0; n < y.Length; n++)
            Assert.Equal(expected[n], y[n], 1e-15);
    }

    [Fact]
    public void RejectsZeroVoices() =>
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.Supersaw(8000, 4, 1000, 10, 0));

    [Fact]
    public void RejectsATopVoiceAboveNyquist() =>
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.Supersaw(8000, 4, 4000, 10));
}
