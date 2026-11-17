using Xunit;

namespace SignalForge.Tests;

/// <summary>Envelope follower (ADR 0238).</summary>
public class EnvelopeFollowerTests
{
    [Fact]
    public void ConstantRisesTowardsItsLevel()
    {
        double[] e = Dsp.EnvelopeFollower([.. Enumerable.Repeat(2.0, 10)], 0.5, 0.9);
        for (int n = 0; n < 10; n++)
            Assert.Equal(2.0 * (1 - Math.Pow(0.5, n + 1)), e[n], 1e-15);
    }
}
