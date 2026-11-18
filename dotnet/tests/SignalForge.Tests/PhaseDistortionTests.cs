using Xunit;

namespace SignalForge.Tests;

/// <summary>Phase-distortion oscillator (ADR 0319).</summary>
public class PhaseDistortionTests
{
    [Fact]
    public void AMiddleKneeIsACosine()
    {
        double[] y = Waveforms.PhaseDistortion(8000, 8, 1000, 0.5);
        for (int n = 0; n < y.Length; n++)
            Assert.Equal(-Math.Cos(2 * Math.PI * n / 8), y[n], 1e-15);
    }

    [Fact]
    public void AQuarterKneePeaksAtTheQuarterCycle() =>
        Assert.Equal(1.0, Waveforms.PhaseDistortion(8000, 8, 1000, 0.25)[2]);

    [Theory]
    [InlineData(0.0)]
    [InlineData(1.0)]
    public void RejectsAKneeAtTheEnds(double knee) =>
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.PhaseDistortion(8000, 4, 1000, knee));
}
