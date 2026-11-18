using Xunit;

namespace SignalForge.Tests;

/// <summary>Karplus–Strong pluck (ADR 0304).</summary>
public class KarplusStrongTests
{
    [Fact]
    public void AveragesTheEchoes()
    {
        Assert.Equal([1, 0, 0.5, 0.5, 0.25, 0.5, 0.375], Dsp.KarplusStrong([1.0], 2, 7, 1.0));
    }

    [Fact]
    public void RejectsAnExcitationLongerThanTheOutput() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.KarplusStrong([1.0, 2.0], 2, 1, 0.9));
}
