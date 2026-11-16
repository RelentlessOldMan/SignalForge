using Xunit;

namespace SignalForge.Tests;

/// <summary>Exceedance levels (conventions: Exceedance levels; ADR 0169).</summary>
public class ExceedanceLevelTests
{
    private static readonly double[] Percents = [10, 50, 90];

    [Fact]
    public void LevelsFallAsThePercentRises()
    {
        var rng = new Random(4);
        var x = new double[4000];
        for (int n = 0; n < x.Length; n++)
            x[n] = rng.NextDouble() - 0.5;
        double[] levels = Measurements.ExceedanceLevels(Measurements.TimeWeighting(x, 8000, 0.125), Percents);
        Assert.True(levels[0] >= levels[1] && levels[1] >= levels[2]);
    }
}
