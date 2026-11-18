using Xunit;

namespace SignalForge.Tests;

/// <summary>Hard-synced sawtooth (ADR 0315).</summary>
public class HardSyncSawtoothTests
{
    [Fact]
    public void TheOutputRepeatsAtTheMasterPeriod()
    {
        double[] y = Waveforms.HardSyncSawtooth(8192, 320, 537.3, 256);
        for (int n = 32; n < y.Length; n++)
            Assert.Equal(y[n - 32], y[n], 1e-12);
    }

    [Theory]
    [InlineData(0.0)]
    [InlineData(-100.0)]
    [InlineData(double.NaN)]
    public void RejectsAMasterThatDoesNotRunForwards(double sync) =>
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.HardSyncSawtooth(8000, 4, 1000, sync));

    [Fact]
    public void RejectsANonFiniteSlave() =>
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.HardSyncSawtooth(8000, 4, double.PositiveInfinity, 1000));
}
