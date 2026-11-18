using Xunit;

namespace SignalForge.Tests;

/// <summary>Damped feedback comb (ADR 0297).</summary>
public class LowpassFeedbackCombTests
{
    [Fact]
    public void NoDampingIsTheFeedbackComb()
    {
        double[] x = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6];
        Assert.Equal(Dsp.CombFilter(x, 3, 0.5, feedback: true), Dsp.LowpassFeedbackComb(x, 3, 0.5, 0.0));
    }

    [Fact]
    public void RejectsDampingOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.LowpassFeedbackComb([1.0], 3, 0.5, 1.0));
}
