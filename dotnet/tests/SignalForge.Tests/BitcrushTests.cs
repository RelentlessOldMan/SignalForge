using Xunit;

namespace SignalForge.Tests;

/// <summary>Bitcrusher (ADR 0266).</summary>
public class BitcrushTests
{
    [Fact]
    public void TwoBitsAndHold()
    {
        double[] y = Dsp.Bitcrush([0.9, -0.9, -0.6, 0.1], 2, hold: 2);
        Assert.Equal([0.5, 0.5, -0.5, -0.5], y);
    }

    [Fact]
    public void RejectsOneBit() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Bitcrush([0.5], 1));
}
