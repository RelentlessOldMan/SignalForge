using Xunit;

namespace SignalForge.Tests;

/// <summary>Band-limited square and triangle (ADR 0309).</summary>
public class BandlimitedOddTests
{
    [Fact]
    public void AQuarterRateNoteIsOneSinusoid()
    {
        double[] sq = Waveforms.BandlimitedSquare(8000, 8, 2000);
        double[] tri = Waveforms.BandlimitedTriangle(8000, 8, 2000);
        for (int n = 0; n < sq.Length; n++)
        {
            Assert.Equal(4 / Math.PI * Math.Sin(Math.PI * n / 2), sq[n], 1e-15);
            Assert.Equal(8 / (Math.PI * Math.PI) * Math.Cos(Math.PI * n / 2), tri[n], 1e-15);
        }
    }

    [Fact]
    public void RejectsZeroFrequency() =>
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.BandlimitedSquare(8000, 4, 0));
}
