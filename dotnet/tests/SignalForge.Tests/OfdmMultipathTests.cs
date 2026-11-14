using System.Numerics;
using System.Text.Json;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Multipath in the OFDM link (conventions: QPSK link, OFDM; ADR 0064).</summary>
public sealed class OfdmMultipathTests
{
    private const double Fs = 4000; // default SymbolRate times SamplesPerSymbol
    private const int U = 63; // default subcarriers: all 64 but DC
    private static readonly int[] Delays = [0, 2, 5, 8];
    private static readonly double[][] Gains = [[1, 0], [0.5, -0.3], [-0.2, 0.4], [0.1, 0.1]];

    private static QpskLinkConfig Ofdm() => new() { NumSymbols = U * 20, PreambleSymbols = U, Modulation = "ofdm" };

    private static QpskLinkConfig Paths(QpskLinkConfig c) => c with { MultipathDelays = Delays, MultipathGains = Gains };

    // |H_k|² of Delays/Gains, the DFT of the impulse response written out
    private static double Power(int k)
    {
        Complex h = Complex.Zero;
        for (int i = 0; i < Delays.Length; i++)
            h += new Complex(Gains[i][0], Gains[i][1]) * Complex.FromPolarCoordinates(1, -2 * Math.PI * k * Delays[i] / 64);
        return h.Magnitude * h.Magnitude;
    }

    private static double Theory(double eb) =>
        Enumerable.Range(-32, 64).Where(k => k != 0).Average(k => Metrics.QpskBerTheory(eb + 10 * Math.Log10(Power(k))));

    [Theory]
    [InlineData(0, 0.0, 0.0)]
    [InlineData(37, 7.3, 1.1)]
    [InlineData(130, -29.0, 3.0)]
    public void NoiselessRecoversEveryBit(int delay, double f, double phase)
    {
        var r = Link.QpskLink(Paths(Ofdm() with { DelaySamples = delay, FrequencyOffsetHz = f, Phase = phase }));
        int start = 4 * r.FrameStart + (int)r.TimingOffset;
        Assert.InRange(start, delay, delay + Delays.Max());
        // the prefix's first samples carry the previous block's echo: f is biased a little
        Assert.Equal(f, r.FrequencyOffsetHz!.Value, 0.05);
        Assert.True(r.Evm!.Rms < 0.01);
        Assert.Equal(0, r.BitErrors.Errors);
    }

    [Theory]
    [InlineData(0, 1.0, 0.0)]
    [InlineData(3, 0.0, -2.0)]
    [InlineData(8, -0.6, 0.8)]
    public void OnePathIsADelayAndAGain(int tap, double re, double im)
    {
        const int delay = 21;
        const double f = 13, phase = -0.4;
        var r = Link.QpskLink(Ofdm() with
        {
            DelaySamples = delay,
            FrequencyOffsetHz = f,
            Phase = phase,
            MultipathDelays = [tap],
            MultipathGains = [[re, im]],
        });
        int total = delay + tap;
        Assert.Equal((total / 4, (double)(total % 4)), (r.FrameStart, r.TimingOffset));
        Assert.Equal(f, r.FrequencyOffsetHz!.Value, 1e-9);
        // the path comes before the carrier offset, which is phase 0 at sample 0
        double want = phase + 2 * Math.PI * f * total / Fs + Math.Atan2(im, re);
        Assert.True(Math.Abs(Math.IEEERemainder(r.PhaseOffset!.Value - want, 2 * Math.PI)) < 1e-9);
        Assert.True(r.Evm!.Rms < 1e-12);
        Assert.Equal(0, r.BitErrors.Errors);
    }

    [Fact]
    public void BerTheoryIsTheMeanOverSubcarriers()
    {
        var r = Link.QpskLink(Paths(Ofdm() with { EbN0Db = 7 }));
        Assert.Equal(Theory(7), r.BerTheory!.Value, 1e-12 * Theory(7));
        var flat = Link.QpskLink(Ofdm() with { EbN0Db = 7, MultipathDelays = [4], MultipathGains = [[0, 1]] });
        Assert.Equal(Metrics.QpskBerTheory(7), flat.BerTheory!.Value, 1e-12 * Metrics.QpskBerTheory(7));
    }

    [Theory]
    [InlineData(4.0)]
    [InlineData(10.0)]
    public void BerBetweenKnownChannelAndEstimateLoss(double eb)
    {
        // each run's channel estimate is shared by all its blocks, so its error does not average out
        // over the blocks: enough preamble blocks keep that spread well inside the bracket
        const int p = 64;
        long errors = 0, compared = 0;
        for (int seed = 0; seed < 3; seed++)
        {
            var r = Link.QpskLink(Paths(Ofdm() with
            {
                NumSymbols = U * 400,
                PreambleSymbols = U * p,
                EbN0Db = eb,
                Seed = seed,
                FrequencyOffsetHz = -20,
                DelaySamples = 11,
            }));
            errors += r.BitErrors.Errors;
            compared += r.BitErrors.Compared;
        }
        double low = Theory(eb), high = Theory(eb - 10 * Math.Log10(1 + 1.0 / p));
        double ber = (double)errors / compared, sd = Math.Sqrt(high / compared);
        Assert.InRange(ber, low - 4 * sd, high + 4 * sd);
    }

    public static TheoryData<QpskLinkConfig> Bad() =>
    [
        Ofdm() with { MultipathDelays = [9], MultipathGains = [[1, 0]] }, // more than cp / 2 = 8
        Ofdm() with { MultipathDelays = [0, 1], MultipathGains = [[1, 0]] },
        Ofdm() with { MultipathDelays = [], MultipathGains = [] },
        Ofdm() with { MultipathDelays = [0] },
        Ofdm() with { MultipathGains = [[1, 0]] },
        Ofdm() with { MultipathDelays = [-1], MultipathGains = [[1, 0]] },
        Ofdm() with { MultipathDelays = [0], MultipathGains = [[1]] },
        Ofdm() with { MultipathDelays = [0], MultipathGains = [[double.NaN, 0]] },
        new QpskLinkConfig { NumSymbols = 64, MultipathDelays = [0], MultipathGains = [[1, 0]] },
    ];

    [Theory]
    [MemberData(nameof(Bad))]
    public void Rejects(QpskLinkConfig c) => Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(c));

    [Fact]
    public void ReportConfig()
    {
        var r = Link.QpskLink(Ofdm() with { MultipathDelays = [0, 3], MultipathGains = [[1, 0], [0, 0.5]] });
        using var doc = JsonDocument.Parse(r.ToJson());
        JsonElement cfg = doc.RootElement.GetProperty("config");
        Assert.Equal([0, 3], cfg.GetProperty("multipath_delays").EnumerateArray().Select(e => e.GetInt32()));
        Assert.Equal(0.5, cfg.GetProperty("multipath_gains")[1][1].GetDouble());
        using var none = JsonDocument.Parse(Link.QpskLink(Ofdm()).ToJson());
        Assert.Equal(JsonValueKind.Null, none.RootElement.GetProperty("config").GetProperty("multipath_gains").ValueKind);
    }
}
