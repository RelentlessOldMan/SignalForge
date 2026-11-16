using Xunit;

namespace SignalForge.Tests;

/// <summary>Delta coefficients (conventions: Delta coefficients; ADR 0158).</summary>
public class DeltaTests
{
    [Theory]
    [InlineData(1)]
    [InlineData(2)]
    [InlineData(3)]
    public void RampInteriorIsTheSlope(int width)
    {
        double[][] frames = Enumerable.Range(0, 20).Select(t => new[] { 0.5 * t - 3, -2.0 * t }).ToArray();
        double[][] d = Spectral.Delta(frames, width);
        for (int t = width; t < 20 - width; t++)
        {
            Assert.Equal(0.5, d[t][0], 1e-12);
            Assert.Equal(-2.0, d[t][1], 1e-12);
        }
    }

    [Fact]
    public void ConstantGivesZeros()
    {
        double[][] frames = Enumerable.Range(0, 5).Select(_ => Enumerable.Repeat(4.0, 3).ToArray()).ToArray();
        Assert.All(Spectral.Delta(frames), row => Assert.All(row, v => Assert.Equal(0.0, v)));
    }

    [Fact]
    public void RejectsRaggedFrames()
    {
        double[][] frames = [[1, 2], [3]];
        Assert.Throws<ArgumentException>(() => Spectral.Delta(frames));
    }
}
