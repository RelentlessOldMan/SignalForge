using Xunit;

namespace SignalForge.Tests;

/// <summary>Octave-band levels (conventions: Octave-band levels; ADR 0168).</summary>
public class OctaveBandLevelTests
{
    [Fact]
    public void AToneAtABandCenterLandsInThatBand()
    {
        const double fs = 48000;
        var x = new double[48000];
        for (int n = 0; n < x.Length; n++)
            x[n] = 2 * Math.Sin(2 * Math.PI * 1000 * n / fs);
        double[] levels = Measurements.OctaveBandLevels(x, fs, 1, 200, 5000);
        double[][] bands = Units.OctaveBands(1, 200, 5000);
        int at = Array.FindIndex(bands, r => r[1] == 1000.0);
        Assert.Equal(2.0, levels[at], 0.02);
        Assert.True(levels.Order().ToArray()[^2] < 0.1);
    }
}
