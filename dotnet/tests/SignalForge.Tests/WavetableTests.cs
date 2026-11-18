using Xunit;

namespace SignalForge.Tests;

/// <summary>Wavetable oscillator (ADR 0308).</summary>
public class WavetableTests
{
    [Fact]
    public void ReadsBetweenThePointsAndWraps()
    {
        Assert.Equal([0, 0.5, 1, 0.5, 0, -0.5, -1, -0.5], Waveforms.Wavetable([0.0, 1, 0, -1], 8000, 8, 1000));
    }

    [Fact]
    public void RejectsAnEmptyTable() =>
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.Wavetable([], 8000, 4, 1000));
}
