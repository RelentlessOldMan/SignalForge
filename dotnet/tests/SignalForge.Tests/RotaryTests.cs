using Xunit;

namespace SignalForge.Tests;

/// <summary>Rotary-speaker effect (ADR 0292).</summary>
public class RotaryTests
{
    [Fact]
    public void IsTheTremoloAndVibratoOfTheBands()
    {
        double[] x = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6, 0.5, 1.3];
        Bands b = Dsp.CrossoverSplit(x, 4, 0.1, 1.0);
        double[] horn = Dsp.Tremolo(Dsp.Vibrato(b.High, 4.0, 3.0, 0.05, 1.0), 0.05, 0.6, 1.0);
        double[] drum = Dsp.Tremolo(b.Low, 0.02, 0.6, 1.0);
        double[] want = [.. horn.Zip(drum, (u, v) => u + v)];
        Assert.Equal(want, Dsp.Rotary(x, 4, 0.1, 0.05, 0.02, 4.0, 3.0, 0.6, 1.0));
    }

    [Fact]
    public void RejectsDepthOverDelay() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Rotary([1.0], 4, 1.0, 0.1, 0.1, 1.0, 2.0, 0.5, 8.0));
}
