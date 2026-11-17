using Xunit;

namespace SignalForge.Tests;

/// <summary>Schmitt trigger (ADR 0244).</summary>
public class SchmittTriggerTests
{
    [Fact]
    public void IgnoresChatterBetweenThresholds()
    {
        byte[] y = Dsp.SchmittTrigger([0.0, 0.6, 0.4, 0.6, -0.6, -0.4, -0.6], -0.5, 0.5);
        Assert.Equal(new byte[] { 0, 1, 1, 1, 0, 0, 0 }, y);
    }

    [Fact]
    public void RejectsEqualThresholds() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.SchmittTrigger([1.0], 0.5, 0.5));
}
