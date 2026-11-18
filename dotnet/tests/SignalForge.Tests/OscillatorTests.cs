using Xunit;

namespace SignalForge.Tests;

/// <summary>Sawtooth, square and triangle oscillators (ADR 0305).</summary>
public class OscillatorTests
{
    [Fact]
    public void TheShapesFollowThePhase()
    {
        Assert.Equal([-1, -0.5, 0, 0.5, -1], Waveforms.Sawtooth(4000, 5, 1000));
        Assert.Equal([1, 1, -1, -1, 1], Waveforms.Square(4000, 5, 1000));
        Assert.Equal([1, 0, -1, 0, 1], Waveforms.Triangle(4000, 5, 1000));
    }

    [Fact]
    public void RejectsDutyAboveOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.Square(8000, 4, 1000, 1.5));
}
