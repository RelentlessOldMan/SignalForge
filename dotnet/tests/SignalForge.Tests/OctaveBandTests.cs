using Xunit;

namespace SignalForge.Tests;

/// <summary>Fractional-octave bands (conventions: Fractional-octave bands; ADR 0167).</summary>
public class OctaveBandTests
{
    [Fact]
    public void BandsTileWithoutGapsAndContain1KhzExactly()
    {
        double[][] rows = Units.OctaveBands(3, 20, 20000);
        Assert.Equal(30, rows.Length);
        for (int i = 1; i < rows.Length; i++)
            Assert.Equal(rows[i - 1][2], rows[i][0], 1e-13 * rows[i][0]);
        Assert.Contains(rows, r => r[1] == 1000.0);
    }

    [Fact]
    public void AnEmptyRangeGivesNoRows() => Assert.Empty(Units.OctaveBands(1, 1100, 1900));
}
