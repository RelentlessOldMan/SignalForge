using Xunit;

namespace SignalForge.Tests;

/// <summary>Mel filterbank (conventions: Mel filterbank; ADR 0155).</summary>
public class MelFilterbankTests
{
    [Theory]
    [InlineData(MelScale.Htk)]
    [InlineData(MelScale.Slaney)]
    public void AdjacentFiltersSumToOneBetweenTheirPeaks(MelScale scale)
    {
        const double Fs = 16000;
        const int Nfft = 512;
        double[][] w = Spectral.MelFilterbank(20, Nfft, Fs, scale: scale);
        double top = Units.HzToMel(Fs / 2, scale);
        double first = Units.MelToHz(top / 21, scale), last = Units.MelToHz(top * 20 / 21, scale);
        for (int k = 0; k <= Nfft / 2; k++)
        {
            double b = k * Fs / Nfft;
            if (b < first || b > last)
                continue;
            Assert.Equal(1.0, w.Sum(row => row[k]), 1e-12);
        }
    }

    [Fact]
    public void AreaNormalizedRowsHaveUnitArea()
    {
        const double Fs = 16000;
        const int Nfft = 1 << 16;
        double[][] w = Spectral.MelFilterbank(10, Nfft, Fs, 300, 6000, areaNormalized: true);
        foreach (double[] row in w)
            Assert.Equal(1.0, row.Sum() * Fs / Nfft, 1e-3);
    }
}
