using Xunit;

namespace SignalForge.Tests;

/// <summary>Bass and treble ratio (conventions: Bass and treble ratio; ADR 0180).</summary>
public class BassTrebleRatioTests
{
    private static readonly double[] Times = [2.1, 1.9, 1.7, 1.6, 1.4, 1.1];

    [Fact]
    public void TheRatiosIgnoreACommonScale()
    {
        double[] scaled = [.. Times.Select(t => 3 * t)];
        Assert.Equal(Measurements.BassRatio(Times), Measurements.BassRatio(scaled), 1e-15);
        Assert.Equal(Measurements.TrebleRatio(Times), Measurements.TrebleRatio(scaled), 1e-15);
    }
}
