using Xunit;

namespace SignalForge.Tests;

/// <summary>Band-limited sawtooth (ADR 0307).</summary>
public class BandlimitedSawtoothTests
{
    [Fact]
    public void AQuarterRateNoteIsOneSine()
    {
        double[] y = Waveforms.BandlimitedSawtooth(8000, 8, 2000);
        for (int n = 0; n < y.Length; n++)
            Assert.Equal(-2 / Math.PI * Math.Sin(Math.PI * n / 2), y[n], 1e-15);
    }

    [Fact]
    public void RejectsZeroFrequency() =>
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.BandlimitedSawtooth(8000, 4, 0));
}
