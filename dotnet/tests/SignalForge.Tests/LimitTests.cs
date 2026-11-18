using Xunit;

namespace SignalForge.Tests;

/// <summary>Lookahead peak limiter (ADR 0269).</summary>
public class LimitTests
{
    [Fact]
    public void GainFallsAheadAndRecovers()
    {
        double[] y = Dsp.Limit([0.5, 0.5, 2.0, 0.5, 0.5], 1.0, 1, 0.5);
        Assert.Equal([0.5, 0.25, 1.0, 0.375, 0.4375], y);
    }

    [Fact]
    public void RejectsZeroThreshold() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Limit([1.0], 0.0, 0, 0.5));
}
