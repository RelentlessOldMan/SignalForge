using Xunit;

namespace SignalForge.Tests;

/// <summary>Coherence significance threshold (conventions: Coherence threshold; ADR 0199).</summary>
public class CoherenceThresholdTests
{
    [Fact]
    public void FallsAsSegmentsGrow()
    {
        double previous = 1;
        for (int k = 2; k < 50; k++)
        {
            double t = Spectral.CoherenceThreshold(k);
            Assert.True(t < previous && t > 0);
            previous = t;
        }
    }
}
