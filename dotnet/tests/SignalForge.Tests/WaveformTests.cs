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

    [Fact]
    public void MultitoneIsTheSumOfTones()
    {
        double[] f = [10, -37.5, 200], a = [1, 0.5, 2], p = [0.1, 2, -3];
        Complex[] x = Waveforms.Multitone(1000, 57, f, a, p);
        double[] r = Waveforms.RealMultitone(1000, 57, f, a, p);
        for (int n = 0; n < 57; n++)
        {
            Complex z = Complex.Zero;
            double v = 0;
            for (int k = 0; k < 3; k++)
            {
                z += Waveforms.Tone(1000, 57, f[k], a[k], p[k])[n];
                v += Waveforms.RealTone(1000, 57, f[k], a[k], p[k])[n];
            }
            Assert.True(Complex.Abs(x[n] - z) <= 1e-14 && Math.Abs(r[n] - v) <= 1e-14);
        }
        Assert.Equal(Waveforms.Multitone(1000, 8, f, [1, 1, 1], [0, 0, 0]), Waveforms.Multitone(1000, 8, f));
    }

    [Fact]
    public void NewmanPhasesLowerTheCrestFactor()
    {
        double[] f = [.. Enumerable.Range(1, 32).Select(k => (double)k)];
        static double Crest(Complex[] x) =>
            x.Max(Complex.Abs) / Math.Sqrt(x.Average(z => z.Magnitude * z.Magnitude));
        double flat = Crest(Waveforms.Multitone(1024, 1024, f));
        Assert.Equal(Math.Sqrt(32), flat, 1e-10);
        Assert.True(Crest(Waveforms.Multitone(1024, 1024, f, phases: Waveforms.NewmanPhases(32))) < 0.4 * flat);
    }

    [Fact]
    public void ChirpInstantaneousFrequencyIsLinear()
    {
        double fs = 1e4, f0 = -1500, f1 = 2500;
        int n = 500;
        Complex[] x = Waveforms.Chirp(fs, n, f0, f1);
        for (int i = 0; i < n - 1; i++)
        {
            double inst = (x[i + 1] * Complex.Conjugate(x[i])).Phase * fs / (2 * Math.PI);
            Assert.Equal(f0 + (f1 - f0) * (i + 0.5) / n, inst, 1e-8);
        }
        double[] r = Waveforms.RealChirp(fs, n, f0, f1, 2, 0.3);
        Complex[] z = Waveforms.Chirp(fs, n, f0, f1, 2, 0.3);
        for (int i = 0; i < n; i++)
            Assert.Equal(z[i].Real, r[i], 1e-13);
        Assert.Empty(Waveforms.Chirp(fs, 0, f0, f1));
    }

    [Theory]
    [InlineData(-13)]
    [InlineData(-1)]
    [InlineData(0)]
    [InlineData(3)]
    [InlineData(1000)]
    public void PulseTrainMatchesItsDefinition(int delay)
    {
        double[] x = Waveforms.PulseTrain(100, 7, 3, 1.5, delay);
        for (int n = 0; n < 100; n++)
            Assert.Equal((((n - delay) % 7) + 7) % 7 < 3 ? 1.5 : 0, x[n]);
    }

    [Fact]
    public void NewGeneratorsRejectBadArguments()
    {
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.Multitone(1, 4, []));
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.RealMultitone(1, 4, [double.NaN]));
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.Multitone(1, 4, [0.1], [double.PositiveInfinity]));
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.Multitone(1, 4, [0.1], phases: [0, 1]));
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.NewmanPhases(0));
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.Chirp(0, 4, 0, 1));
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.Chirp(1, -1, 0, 1));
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.RealChirp(1, 4, double.NaN, 1));
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.Chirp(1, 4, 0, 1, double.NaN));
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.Chirp(1, 4, 0, 1, 1, double.PositiveInfinity));
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.PulseTrain(4, 0, 0));
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.PulseTrain(4, 2, 3));
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.PulseTrain(4, 2, -1));
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.PulseTrain(-1, 2, 1));
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.PulseTrain(4, 2, 1, double.NaN));
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.Tone(1, 4, double.NaN));
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.RealTone(1, 4, 0.1, double.PositiveInfinity));
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.Tone(1, 4, 0.1, 1, double.NaN));
    }
}
