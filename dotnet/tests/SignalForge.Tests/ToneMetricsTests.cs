using System.Numerics;

namespace SignalForge.Tests;

public class ToneMetricsTests
{
    private static double[] Cosines(int n, double dc, params (double Bin, double Amplitude)[] tones) =>
        [.. Enumerable.Range(0, n).Select(i => dc + tones.Sum(t => t.Amplitude * Math.Cos(2 * Math.PI * t.Bin * i / n)))];

    [Fact]
    public void GroupPowersAddUpToTheSpectrum()
    {
        double[] x = Cosines(256, 0.2, (17.3, 1.0), (34.6, 0.01));
        var m = Measurements.ToneMetrics(x, 256);
        var d = Spectral.WelchPsd(x, 256, window: WindowType.BlackmanHarris);
        double total = m.SignalPower + m.HarmonicPower + m.NoisePower + m.DcPower;
        Assert.Equal(d.Psd.Sum() * d.BinWidth, total, 1e-12);
    }

    [Fact]
    public void AnOffBinToneReadsItsPowerAndFrequency()
    {
        double fs = 48000, f = 100.3 * fs / 1024;
        var m = Measurements.ToneMetrics(Waveforms.RealTone(fs, 1024, f, 0.5), fs);
        Assert.Equal(0.125, m.SignalPower, 0.125e-6);
        Assert.Equal(f, m.FundamentalFrequency, 0.01 * fs / 1024);
    }

    [Fact]
    public void WhiteNoiseSetsTheSnr()
    {
        var rng = new Random(7);
        const double sigma = 0.01;
        double[] x = Cosines(8192, 0, (1000.5, 1.0));
        for (int i = 0; i < x.Length; i++)  // Box-Muller
            x[i] += sigma * Math.Sqrt(-2 * Math.Log(1 - rng.NextDouble())) * Math.Cos(2 * Math.PI * rng.NextDouble());
        var m = Measurements.ToneMetrics(x, 8192, numHarmonics: 0);
        Assert.Equal(10 * Math.Log10(0.5 / (sigma * sigma)), m.SnrDb, 0.5);
        Assert.Equal(double.NegativeInfinity, m.ThdDb);
        Assert.Equal(m.SnrDb, m.SinadDb);
    }

    [Theory]
    [InlineData(0.0, 1)]
    [InlineData(8.6, 3)]
    [InlineData(20.0, 7)]
    public void TheDefaultKaiserWidthIsTheMainLobe(double beta, int width)
    {
        double[] x = Cosines(128, 0, (30, 1.0), (47, 1e-3));
        Assert.Equal(Measurements.ToneMetrics(x, 128, WindowType.Kaiser, beta, width),
            Measurements.ToneMetrics(x, 128, WindowType.Kaiser, beta));
    }

    [Fact]
    public void ComplexInputIsTwoSided()
    {
        Complex[] x = [.. Waveforms.Tone(64, 64, -12, 0.5).Zip(Waveforms.Tone(64, 64, 20, 0.01), (a, b) => a + b)];
        var m = Measurements.ToneMetrics(x, 64, WindowType.Hann, numHarmonics: 1);
        Assert.Equal(-12.0, m.FundamentalFrequency, 1e-12);
        Assert.Equal(0.25, m.SignalPower, 1e-12);
        Assert.Equal(0.0, m.HarmonicPower, 1e-20);
        Assert.Equal(1e-4, m.NoisePower, 1e-16);
    }

    [Fact]
    public void BadArguments()
    {
        double[] x = [.. Enumerable.Range(0, 32).Select(i => Math.Cos(1.2 * i))];
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ToneMetrics(x, 32, width: -1));
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ToneMetrics(x, 32, numHarmonics: -1));
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ToneMetrics(x, 32, fundamental: double.PositiveInfinity));
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ToneMetrics(x, 32, WindowType.Hann, beta: 2));
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ToneMetrics(x, 32, WindowType.Kaiser));
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ToneMetrics(x.AsSpan(0, 1), 32));
    }

    [Fact]
    public void SfdrTakesTheStrongestSpurAndNeverDc()
    {
        double[] x = Cosines(1024, 0.5, (100, 1.0), (200, 0.03), (371.4, 0.001));
        var s = Measurements.Sfdr(x, 1024, numSpurs: 2);
        Assert.Equal(100.0, s.CarrierFrequency, 1e-9);
        Assert.Equal(200.0, s.SpurFrequencies[0], 1e-9);
        Assert.Equal(-20 * Math.Log10(0.03), s.SfdrDb, 1e-9);
        Assert.Equal(371.4, s.SpurFrequencies[1], 0.01);
        Assert.Equal(20 * Math.Log10(0.001), s.SpurDbc[1], 1e-3);
        var t = Measurements.ToneMetrics(x, 1024);
        Assert.Equal(t.SignalPower, s.CarrierPower);
        Assert.Throws<ArgumentOutOfRangeException>(() => Measurements.Sfdr(x, 1024, numSpurs: 0));
    }
}
