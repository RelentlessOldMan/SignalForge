using Xunit;

namespace SignalForge.Tests;

/// <summary>Two-band splitter (ADR 0285).</summary>
public class CrossoverSplitTests
{
    [Fact]
    public void MatchesTheCrossoverFilters()
    {
        double[] x = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6];
        Bands b = Dsp.CrossoverSplit(x, 4, 0.1, 1.0);
        Crossover lr = Dsp.LinkwitzRiley(4, 0.1, 1.0);
        Assert.Equal(new IirFilter(lr.Low).Process(x), b.Low);
        Assert.Equal(new IirFilter(lr.High).Process(x), b.High);
    }

    [Fact]
    public void RejectsEmptySamples() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.CrossoverSplit([], 4, 1.0, 8.0));
}
