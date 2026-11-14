using Xunit;

namespace SignalForge.Tests;

/// <summary>The frame search in blocks (conventions: QPSK link, Receiver, step 3; ADR 0068).</summary>
public sealed class FrameSearchTests
{
    private static readonly int L = Dsp.RrcTaps(0.35, 4, 10).Length;

    [Fact]
    public void ALongPreambleFindsTheFrameThroughAFrequencyError()
    {
        // a 1000-symbol preamble is one second at 1 kHz; coherently over it, a 1 Hz residual turns
        // the correlation a full cycle (ADR 0068). Strong inter-symbol interference puts the coarse
        // QPSK frequency estimate about 1.3 Hz off.
        for (int seed = 0; seed < 10; seed++)
        {
            var c = new QpskLinkConfig
            {
                NumSymbols = 6000,
                PreambleSymbols = 1000,
                EbN0Db = 6,
                Seed = seed,
                MultipathDelays = [0, 3, 7],
                MultipathGains = [[1, 0], [0.4, -0.3], [-0.2, 0.1]],
                EqualizerTaps = 11,
            };
            Assert.Equal((L - 1) / 4, Link.QpskLink(c).FrameStart);
        }
    }

    [Theory]
    [InlineData(200, 32, 7)]
    [InlineData(100, 7, 13)]
    [InlineData(33, 32, 2)]
    public void NoiselessBlocksFindTheTrueStart(int pre, int blk, int delay)
    {
        var r = Link.QpskLink(new QpskLinkConfig
        {
            NumSymbols = 600,
            PreambleSymbols = pre,
            PhaseBlockSymbols = blk,
            DelaySamples = delay,
            FrequencyOffsetHz = 30,
            Phase = -2,
        });
        Assert.Equal((L - 1 + delay) / 4, r.FrameStart);
        Assert.Equal(0, r.BitErrors.Errors);
    }
}
