using Xunit;

namespace SignalForge.Tests;

/// <summary>ADSR envelope (ADR 0303).</summary>
public class AdsrTests
{
    [Fact]
    public void RunsEveryStage()
    {
        Assert.Equal([0, 0.5, 1, 0.75, 0.5, 0.5, 0.25, 0, 0], Waveforms.Adsr(9, 2, 2, 0.5, 2, 5));
    }

    [Fact]
    public void RejectsSustainAboveOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.Adsr(8, 2, 2, 1.5, 2, 5));
}
