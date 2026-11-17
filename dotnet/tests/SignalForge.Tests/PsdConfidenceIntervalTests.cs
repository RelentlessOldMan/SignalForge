using Xunit;

namespace SignalForge.Tests;

/// <summary>PSD confidence interval (conventions: PSD confidence interval; ADR 0201).</summary>
public class PsdConfidenceIntervalTests
{
    [Fact]
    public void TwoDofMatchesTheClosedForm()
    {
        // ν = 2: q(p) = −2 ln(1 − p)
        var ci = Spectral.PsdConfidenceInterval([1.0], 2, 0.9);
        Assert.Equal(2 / (2 * Math.Log(20)), ci.Lower[0], 1e-13);
        Assert.Equal(2 / (-2 * Math.Log(0.95)), ci.Upper[0], 1e-11);
    }

    [Fact]
    public void IntervalNarrowsAsDofGrows()
    {
        double previous = double.PositiveInfinity;
        foreach (double nu in new[] { 0.5, 1, 3.3, 10, 100, 1000, 10000 })
        {
            var ci = Spectral.PsdConfidenceInterval([1.0], nu);
            Assert.True(ci.Lower[0] < 1 && ci.Upper[0] > 1);
            double width = ci.Upper[0] / ci.Lower[0];
            Assert.True(width < previous);
            previous = width;
        }
    }
}
