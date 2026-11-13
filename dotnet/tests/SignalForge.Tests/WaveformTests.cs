using System.Numerics;

namespace SignalForge.Tests;

public class WaveformTests
{
    [Fact]
    public void TonePowerMatchesAmplitude()
    {
        var x = Waveforms.Tone(1000, 1000, 125, amplitude: 3);
        Assert.Equal(9.0, x.Average(s => s.Magnitude * s.Magnitude), 1e-12);
    }

    [Fact]
    public void RealToneIsRealPartOfComplex()
    {
        var c = Waveforms.Tone(48000, 64, 1000, 0.5, 0.3);
        var r = Waveforms.RealTone(48000, 64, 1000, 0.5, 0.3);
        for (int i = 0; i < r.Length; i++)
            Assert.Equal(c[i].Real, r[i], 1e-15);
    }

    [Fact]
    public void SpanOverloadFillsDestination()
    {
        Span<Complex> d = stackalloc Complex[4];
        Waveforms.Tone(d, 4, 1);
        Assert.Equal(-1.0, d[2].Real, 1e-15);
    }

    [Theory]
    [InlineData(7)]
    [InlineData(9)]
    [InlineData(11)]
    [InlineData(15)]
    [InlineData(20)]
    public void PrbsIsMaximalLength(int order)
    {
        int period = (1 << order) - 1;
        var bits = Waveforms.Prbs(order, 2 * period);
        Assert.Equal(1 << (order - 1), bits.Take(period).Sum(b => b));
        Assert.True(bits.AsSpan(0, period).SequenceEqual(bits.AsSpan(period)));
        // No shorter period: the run of all ones appears once per period (counted cyclically).
        int runs = 0, len = 0;
        for (int i = 0; i < period + order - 1; i++)
        {
            len = bits[i % period] == 1 ? len + 1 : 0;
            if (len == order)
                runs++;
        }
        Assert.Equal(1, runs);
    }

    [Theory]
    [InlineData(23)]
    [InlineData(31)]
    public void LongOrdersStartWithSeed(int order) =>
        Assert.All(Waveforms.Prbs(order, order + 5).Take(order), b => Assert.Equal(1, b));

    [Fact]
    public void PrbsInvertAndSeedChecks()
    {
        var a = Waveforms.Prbs(9, 100);
        var b = Waveforms.Prbs(9, 100, invert: true);
        Assert.All(Enumerable.Range(0, 100), i => Assert.Equal(1, a[i] ^ b[i]));
        Assert.Throws<ArgumentOutOfRangeException>(() => Waveforms.Prbs(9, 10, seed: 1u << 9));
        Assert.Empty(Waveforms.Prbs(7, 0));
    }
}
