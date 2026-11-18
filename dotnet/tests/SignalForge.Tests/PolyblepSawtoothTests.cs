using Xunit;

namespace SignalForge.Tests;

/// <summary>PolyBLEP sawtooth (ADR 0310).</summary>
public class PolyblepSawtoothTests
{
    [Fact]
    public void OnlyTheSamplesNextToTheJumpChange()
    {
        double[] naive = Waveforms.Sawtooth(8000, 16, 1000, 1, 0.0625);
        double[] y = Waveforms.PolyblepSawtooth(8000, 16, 1000, 1, 0.0625);
        for (int n = 0; n < y.Length; n++)
        {
            if (n % 8 is 0 or 7)
                Assert.NotEqual(naive[n], y[n]);
            else
                Assert.Equal(naive[n], y[n]);
        }
    }

    [Fact]
    public void RejectsAFrequencyAboveNyquist() =>
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.PolyblepSawtooth(8000, 4, 4001));
}
