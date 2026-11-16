using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Gammatone impulse response (conventions: Gammatone; ADR 0161).</summary>
public class GammatoneTests
{
    [Fact]
    public void UnitGainAtCenterAndOrder4Bandwidth()
    {
        const double Fs = 16000, Fc = 2000;
        double[] h = Dsp.Gammatone(Fc, Fs, 2000);
        double Gain(double f)
        {
            Complex sum = Complex.Zero;
            for (int n = 0; n < h.Length; n++)
                sum += h[n] * Complex.Exp(new Complex(0, -2 * Math.PI * f / Fs * n));
            return sum.Magnitude;
        }
        Assert.Equal(1.0, Gain(Fc), 1e-12);
        double want = 2 * Math.Sqrt(Math.Pow(2, 0.25) - 1) * 1.019 * Units.ErbBandwidth(Fc);
        double lo = Fc, hi = Fc;
        while (Gain(lo) >= 1 / Math.Sqrt(2))
            lo -= 1;
        while (Gain(hi) >= 1 / Math.Sqrt(2))
            hi += 1;
        Assert.InRange(hi - lo, 0.98 * want, 1.02 * want);
    }
}
