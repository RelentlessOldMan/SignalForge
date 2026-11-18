using Xunit;

namespace SignalForge.Tests;

/// <summary>Phaser (ADR 0274).</summary>
public class PhaserTests
{
    [Fact]
    public void DryAtZeroMix()
    {
        double[] x = [0.3, -0.7, 1.1, 0.4];
        Assert.Equal(x, Dsp.Phaser(x, 3, 1.0, 3.0, 1.0, 8.0, 0.0));
    }

    [Fact]
    public void RejectsHighAtNyquist() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Phaser([1.0], 2, 1.0, 4.0, 1.0, 8.0, 0.5));
}
