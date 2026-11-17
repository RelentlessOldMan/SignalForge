using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>LPC cepstrum (conventions: LPC cepstrum; ADR 0207).</summary>
public class LpcCepstrumTests
{
    [Fact]
    public void SeriesGivesTheModelLogSpectrum()
    {
        double[] a = [1.0, -1.2, 0.6, -0.1];
        double error = 0.7;
        var c = Dsp.LpcCepstrum(a, error, 200);
        for (int i = 0; i <= 16; i++)
        {
            double w = Math.PI * i / 16;
            Complex big = Complex.Zero;
            for (int j = 0; j < a.Length; j++)
                big += a[j] * Complex.Exp(new Complex(0, -w * j));
            double model = Math.Log(error / (big.Magnitude * big.Magnitude));
            double series = 0;
            for (int n = 0; n < c.Length; n++)
                series += 2 * c[n] * Math.Cos(w * n);
            Assert.Equal(model, series, 1e-10);
        }
    }
}
