using Xunit;

namespace SignalForge.Tests;

/// <summary>16-QAM and 8-PSK error-rate theory: limits, the textbook approximations at high SNR, and
/// Monte-Carlo runs through the mappers, AWGN and the hard demappers (conventions: EVM and BER).</summary>
public class ErrorRateTests
{
    private static Func<double, double> Theory(string name) => name switch
    {
        "qam16_ber" => Metrics.Qam16BerTheory,
        "qam16_ser" => Metrics.Qam16SerTheory,
        "psk8_ber" => Metrics.Psk8BerTheory,
        _ => Metrics.Psk8SerTheory,
    };

    [Theory]
    [InlineData("qam16_ber", 0.5)]
    [InlineData("qam16_ser", 15.0 / 16)]
    [InlineData("psk8_ber", 0.5)]
    [InlineData("psk8_ser", 7.0 / 8)]
    public void Limits(string name, double guess)
    {
        Func<double, double> f = Theory(name);
        Assert.Equal(guess, f(double.NegativeInfinity), 1e-15);
        Assert.Equal(0.0, f(double.PositiveInfinity));
        Assert.Equal(0.0, f(5000));
        for (double db = -10; db < 19.5; db += 0.5)
            Assert.True(f(db) > f(db + 0.5), $"{name} at {db} dB");
        Assert.ThrowsAny<ArgumentException>(() => f(double.NaN));
    }

    // Q(x) = ½·erfc(x/√2), through the public QPSK curve ½·erfc(√(Eb/N0)) at Eb/N0 = x²/2.
    private static double Q(double x) => Metrics.QpskBerTheory(10 * Math.Log10(x * x / 2));

    [Theory]
    [InlineData(14.0)]
    [InlineData(18.0)]
    public void HighSnrApproximations(double db)
    {
        double esN0 = 3 * Math.Pow(10, db / 10);
        double approx = 2 * Q(Math.Sqrt(2 * esN0) * Math.Sin(Math.PI / 8));
        Assert.Equal(1, Metrics.Psk8SerTheory(db) / approx, 1e-3);
        Assert.Equal(1, Metrics.Psk8BerTheory(db) / (Metrics.Psk8SerTheory(db) / 3), 1e-3);
        Assert.Equal(1, Metrics.Qam16BerTheory(db) / (Metrics.Qam16SerTheory(db) / 4), 1e-3);
    }

    [Theory]
    [InlineData(4, 150_000)]
    [InlineData(3, 200_000)]
    public void MonteCarlo(int k, int symbols)
    {
        const double ebN0Db = 8;
        byte[] bits = Waveforms.Prbs(23, k * symbols);
        var tx = k == 4 ? Modulation.Qam16Map(bits) : Modulation.Psk8Map(bits);
        var rx = Channel.Awgn(tx, ebN0Db + 10 * Math.Log10(k), 1, 12, 1.0);
        byte[] got = k == 4 ? Modulation.Qam16DemapHard(rx) : Modulation.Psk8DemapHard(rx);
        int bitErrors = 0, symbolErrors = 0;
        for (int s = 0; s < symbols; s++)
        {
            int wrong = 0;
            for (int i = s * k; i < (s + 1) * k; i++)
                wrong += got[i] != bits[i] ? 1 : 0;
            bitErrors += wrong;
            symbolErrors += wrong > 0 ? 1 : 0;
        }
        double ber = k == 4 ? Metrics.Qam16BerTheory(ebN0Db) : Metrics.Psk8BerTheory(ebN0Db);
        double ser = k == 4 ? Metrics.Qam16SerTheory(ebN0Db) : Metrics.Psk8SerTheory(ebN0Db);
        // about 4000 to 5500 errors of each kind: 3 sigma is under 5 %
        Assert.Equal(1, bitErrors / (double)(k * symbols) / ber, 0.06);
        Assert.Equal(1, symbolErrors / (double)symbols / ser, 0.06);
    }
}
