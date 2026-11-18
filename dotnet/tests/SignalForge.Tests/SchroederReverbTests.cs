using Xunit;

namespace SignalForge.Tests;

/// <summary>Schroeder reverberator (ADR 0295).</summary>
public class SchroederReverbTests
{
    [Fact]
    public void OneCombIsTheFeedbackComb()
    {
        double[] x = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6];
        Assert.Equal(Dsp.CombFilter(x, 3, 0.5, feedback: true), Dsp.SchroederReverb(x, [3], [0.5], [], 0.5, 1.0));
    }

    [Fact]
    public void RejectsMismatchedGains() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.SchroederReverb([1.0], [3, 5], [0.5], [], 0.5, 0.5));
}
