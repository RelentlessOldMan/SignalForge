using Xunit;

namespace SignalForge.Tests;

/// <summary>DPW sawtooth (ADR 0317).</summary>
public class DpwSawtoothTests
{
    [Fact]
    public void IsTheMeanOfTwoNaiveSamplesAwayFromTheWrap()
    {
        double[] naive = Waveforms.Sawtooth(8000, 400, 20);
        double[] y = Waveforms.DpwSawtooth(8000, 400, 20);
        for (int n = 1; n < 399; n++)
            Assert.Equal(naive[n] - (20.0 / 8000), y[n], 1e-12);
    }

    [Fact]
    public void ZeroFrequencyIsTheNaiveShape() =>
        Assert.Equal(Waveforms.Sawtooth(8000, 4, 0, 1, 0.75), Waveforms.DpwSawtooth(8000, 4, 0, 1, 0.75));

    [Fact]
    public void RejectsAFrequencyAboveNyquist() =>
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.DpwSawtooth(8000, 4, 4001));
}
