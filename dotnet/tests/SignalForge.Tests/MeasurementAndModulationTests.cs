using System.Numerics;

namespace SignalForge.Tests;

public class MeasurementTests
{
    [Fact]
    public void RealSinePaprIs3Db()
    {
        var s = Measurements.PowerStats(Waveforms.RealTone(1000, 1000, 50));
        Assert.Equal(0.5, s.MeanPower, 1e-12);
        Assert.Equal(10 * Math.Log10(2), s.PaprDb, 1e-9);
        Assert.True(s.Dc.Magnitude < 1e-12);
    }

    [Fact]
    public void ComplexDcAndPeak()
    {
        var s = Measurements.PowerStats(new Complex[] { new(1, 2), new(3, -1) });
        Assert.Equal(new Complex(2, 0.5), s.Dc);
        Assert.Equal(1, s.PeakIndex);
    }

    [Fact]
    public void EmptyThrows() =>
        Assert.Throws<ArgumentException>(() => Measurements.PowerStats(ReadOnlySpan<double>.Empty));
}

public class ModulationTests
{
    [Fact]
    public void QpskRoundTripAndUnitEnergy()
    {
        var bits = Waveforms.Prbs(9, 1022);
        var s = Modulation.QpskMap(bits);
        Assert.Equal(1.0, s.Average(x => x.Magnitude * x.Magnitude), 1e-12);
        Assert.Equal(bits, Modulation.QpskDemapHard(s));
    }

    [Fact]
    public void RotationBy90DegreesCostsOneBitPerSymbol()
    {
        byte[] bits = [0, 0, 0, 1, 1, 0, 1, 1];
        var rotated = Modulation.QpskMap(bits).Select(x => x * Complex.ImaginaryOne).ToArray();
        Assert.Equal(4, Metrics.BitErrors(bits, Modulation.QpskDemapHard(rotated)).Errors);
    }

    [Fact]
    public void BitErrorsEmpty()
    {
        var r = Metrics.BitErrors([], []);
        Assert.Equal(0, r.Compared);
        Assert.True(double.IsNaN(r.Rate));
    }
}

public class SignalTests
{
    [Fact]
    public void CopiesSamplesAndKeepsMetadata()
    {
        double[] raw = [1, 2, 3];
        var s = new Signal<double>(raw, 10, units: "V", impedance: 50);
        raw[0] = 99;
        Assert.Equal(1.0, s.Samples[0]);
        Assert.Equal(3, s.Length);
        Assert.Equal(0.3, s.Duration, 1e-15);
    }

    [Fact]
    public void TimesAndWithSamples()
    {
        var s = new Signal<Complex>(new Complex[4], 2, centerFrequency: 1e9, timeOrigin: 1,
            metadata: new Dictionary<string, object?> { ["a"] = 1 });
        Assert.Equal([1.0, 1.5, 2.0, 2.5], s.Times());
        var t = s.WithSamples([Complex.ImaginaryOne]);
        Assert.Equal(1e9, t.CenterFrequency);
        Assert.Equal(1, t.Length);
        Assert.Equal(1, t.Metadata["a"]);
    }

    [Fact]
    public void Validation()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new Signal<double>([1.0], 0));
        Assert.Throws<ArgumentOutOfRangeException>(() => new Signal<double>([1.0], 1, impedance: -1));
    }
}
