using Xunit;

namespace SignalForge.Tests;

/// <summary>Coherence confidence interval (conventions: Coherence confidence interval; ADR 0202).</summary>
public class CoherenceConfidenceIntervalTests
{
    [Fact]
    public void ContainsTheEstimateAndNarrowsWithSegments()
    {
        double[] g2 = [0.0, 0.1, 0.5, 0.9, 0.999];
        var previous = Enumerable.Repeat(double.PositiveInfinity, g2.Length).ToArray();
        foreach (int k in new[] { 2, 4, 16, 64, 1024 })
        {
            var ci = Spectral.CoherenceConfidenceInterval(g2, k);
            for (int i = 0; i < g2.Length; i++)
            {
                Assert.True(ci.Lower[i] <= g2[i] && ci.Upper[i] >= g2[i]);
                Assert.True(ci.Lower[i] >= 0 && ci.Upper[i] <= 1);
                double width = ci.Upper[i] - ci.Lower[i];
                Assert.True(width < previous[i]);
                previous[i] = width;
            }
        }
    }
}
