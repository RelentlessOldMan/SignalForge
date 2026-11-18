using Xunit;

namespace SignalForge.Tests;

/// <summary>Bandlimited impulse train (ADR 0320).</summary>
public class BlitTests
{
    [Fact]
    public void MatchesTheCosineSum()
    {
        // fs/8: harmonics 1, 2 and 3, M = 7.
        double[] y = Waveforms.Blit(8000, 16, 1000, 1, 0.1);
        for (int n = 0; n < y.Length; n++)
        {
            double t = (1000 * (n / 8000.0)) + 0.1;
            double u = t - Math.Floor(t);
            double s = 1;
            for (int m = 1; m <= 3; m++)
                s += 2 * Math.Cos(2 * Math.PI * m * u);
            Assert.Equal(s / 7, y[n], 1e-14);
        }
    }

    [Fact]
    public void PeaksAtTheAmplitude() => Assert.Equal(0.6, Waveforms.Blit(44100, 1, 441, 0.6)[0]);

    [Fact]
    public void RejectsAZeroFrequency() =>
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.Blit(8000, 4, 0));
}
