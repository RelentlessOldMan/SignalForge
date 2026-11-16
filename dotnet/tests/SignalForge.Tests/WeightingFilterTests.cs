using Xunit;

namespace SignalForge.Tests;

/// <summary>A and C weighting filters (conventions: Weighting filters; ADR 0165).</summary>
public class WeightingFilterTests
{
    [Theory]
    [InlineData(8000.0, true)]
    [InlineData(48000.0, true)]
    [InlineData(192000.0, true)]
    [InlineData(8000.0, false)]
    [InlineData(48000.0, false)]
    [InlineData(192000.0, false)]
    public void ResponseIsTheCurveAtTheWarpedFrequency(double fs, bool aCurve)
    {
        double[][] sos = aCurve ? Dsp.AWeightingSos(fs) : Dsp.CWeightingSos(fs);
        Func<double, double> curve = aCurve ? Units.AWeighting : Units.CWeighting;
        double Warped(double x) => fs / Math.PI * Math.Tan(Math.PI * x / fs);
        var f = new double[200];
        for (int i = 0; i < f.Length; i++)
            f[i] = 10 + (0.45 * fs - 10) * i / (f.Length - 1);
        var h = Dsp.SosResponse(sos, f, fs);
        double reference = curve(Warped(1000));
        for (int i = 0; i < f.Length; i++)
        {
            double want = curve(Warped(f[i])) - reference;
            Assert.Equal(want, 20 * Math.Log10(h[i].Magnitude), 1e-9 + 1e-9 * Math.Abs(want));
        }
        Assert.Equal(1.0, Dsp.SosResponse(sos, [1000.0], fs)[0].Magnitude, 1e-12);
    }
}
