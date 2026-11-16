using Xunit;

namespace SignalForge.Tests;

/// <summary>Speech transmission index (conventions: Speech transmission index; ADR 0177).</summary>
public class SpeechTransmissionIndexTests
{
    [Fact]
    public void AUniformMtfGivesItsTransmissionIndex()
    {
        const double m = 0.7;
        var mtf = new double[7][];
        for (int k = 0; k < 7; k++)
            mtf[k] = Enumerable.Repeat(m, 14).ToArray();
        Assert.Equal((10 * Math.Log10(m / (1 - m)) + 15) / 30, Measurements.SpeechTransmissionIndex(mtf), 1e-14);
    }

    [Fact]
    public void ARaggedMatrixIsRejected()
    {
        var mtf = new double[7][];
        for (int k = 0; k < 7; k++)
            mtf[k] = new double[k == 6 ? 1 : 2];
        Assert.Throws<ArgumentException>(() => Measurements.SpeechTransmissionIndex(mtf));
    }
}
