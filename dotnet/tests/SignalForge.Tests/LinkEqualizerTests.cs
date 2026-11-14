using Xunit;

namespace SignalForge.Tests;

/// <summary>The LMS equalizer in the single-carrier link (conventions: QPSK link; ADR 0067).</summary>
public sealed class LinkEqualizerTests
{
    private static readonly int[] Delays = [0, 2, 5];
    private static readonly double[][] Gains = [[1, 0], [0.3, 0.2], [-0.1, 0]];
    private const double AllowanceDb = 1.0; // noise enhancement and misadjustment: a test allowance, not derived

    private static QpskLinkConfig Eq(string modulation = "qpsk") => new()
    {
        Modulation = modulation,
        NumSymbols = 4000,
        PreambleSymbols = 500,
        PhaseBlockSymbols = 64,
        DelaySamples = 3,
        FrequencyOffsetHz = 5,
        Phase = 0.7,
        EqualizerTaps = 11,
        MultipathDelays = Delays,
        MultipathGains = Gains,
    };

    private static QpskLinkConfig Flat(QpskLinkConfig c) => c with { MultipathDelays = null, MultipathGains = null };

    private static int Bits(string m) => m switch { "qam16" => 4, "psk8" => 3, "qam64" => 6, _ => 2 };

    private static double Theory(string m, double eb) => m switch
    {
        "qam16" => Metrics.Qam16BerTheory(eb),
        "psk8" => Metrics.Psk8BerTheory(eb),
        "qam64" => Metrics.Qam64BerTheory(eb),
        _ => Metrics.QpskBerTheory(eb),
    };

    // the raised cosine at t symbols, written out (no edge point is used here)
    private static double Rho(double t, double beta)
    {
        double sinc = t == 0 ? 1 : Math.Sin(Math.PI * t) / (Math.PI * t);
        return sinc * Math.Cos(Math.PI * beta * t) / (1 - (2 * beta * t) * (2 * beta * t));
    }

    [Theory]
    [InlineData("qpsk")]
    [InlineData("qam16")]
    [InlineData("psk8")]
    [InlineData("qam64")]
    public void NoiselessMultipathIsRecovered(string mod)
    {
        var r = Link.QpskLink(Eq(mod));
        Assert.Equal(0, r.BitErrors.Errors);
        Assert.Equal(Bits(mod) * (4000 - 500), r.BitErrors.Compared); // the preamble does not count
        Assert.Equal(3500, r.Evm!.NumSymbols);
        Assert.True(r.Evm.Rms < 0.03);
        Assert.Null(r.BerTheory);
    }

    [Theory]
    [InlineData("qam16")]
    [InlineData("qam64")]
    public void HeldTapsLeaveTheEchoes(string mod)
    {
        // step 0 holds the taps on the chain's own sample, so the echoes stay as interference; with
        // no carrier offset to take out, the flat channel is still clean
        var c = Eq(mod) with { EqualizerStep = 0, FrequencyOffsetHz = 0, Phase = 0 };
        Assert.True(Link.QpskLink(c).BitErrors.Errors > 0);
        Assert.Equal(0, Link.QpskLink(Flat(c)).BitErrors.Errors);
        Assert.Equal(0, Link.QpskLink(Eq(mod)).BitErrors.Errors);
    }

    [Fact]
    public void FlatChannelWithTheEqualizer()
    {
        var r = Link.QpskLink(Flat(Eq()));
        Assert.Equal(0, r.BitErrors.Errors);
        Assert.True(r.Evm!.Rms < 0.02);
        Assert.Equal((Dsp.RrcTaps(0.35, 4, 10).Length - 1 + 3) / 4, r.FrameStart);
    }

    [Fact]
    public void EstimatesBeforeTheEqualizerAreUnchanged()
    {
        // the equalizer replaces step 7: timing, frame start and phase are the chain's (the frequency
        // is the preamble's, ADR 0070: LinkDfeTests)
        var with = Link.QpskLink(Flat(Eq()));
        var without = Link.QpskLink(Flat(Eq()) with { EqualizerTaps = null });
        Assert.Equal(without.TimingOffset, with.TimingOffset);
        Assert.Equal(without.FrameStart, with.FrameStart);
        Assert.Equal(without.PhaseOffset!.Value, with.PhaseOffset!.Value, 1e-6); // f₁ differs (ADR 0071)
    }

    public static TheoryData<int[], double[][], double> Bounds() => new()
    {
        // by hand: one path is a gain, E_h = |g|^2
        { [3], [[0.6, -0.8]], 1.0 },
        { [0], [[0.5, 0]], 0.25 },
        // paths a whole symbol (4 samples) apart: rho(1) = 0, so the energies add
        { [0, 4], [[1, 0], [0, 0.5]], 1.25 },
        { [0, 8], [[0.8, 0], [0.6, 0]], 1.0 },
        // half a symbol apart: 1 + |g|^2 + 2 Re(g) rho(1/2)
        { [0, 2], [[1, 0], [0.3, 0.2]], 1 + 0.13 + 2 * 0.3 * Rho(0.5, 0.35) },
    };

    [Theory]
    [MemberData(nameof(Bounds))]
    public void BerTheoryIsTheMatchedFilterBound(int[] delays, double[][] gains, double eh)
    {
        foreach (string mod in new[] { "qpsk", "qam16", "psk8", "qam64" })
        {
            var r = Link.QpskLink(Eq(mod) with { EbN0Db = 7, NumSymbols = 600, MultipathDelays = delays, MultipathGains = gains });
            double want = Theory(mod, 7 + 10 * Math.Log10(eh));
            Assert.Equal(want, r.BerTheory!.Value, want * 1e-12);
        }
    }

    [Fact]
    public void BerTheoryWithoutMultipathIsTheFlatTheory() =>
        Assert.Equal(Metrics.QpskBerTheory(7), Link.QpskLink(Flat(Eq()) with { EbN0Db = 7, NumSymbols = 600 }).BerTheory);

    [Fact]
    public void PathsThatCancelGiveOneHalf()
    {
        // two equal paths in antiphase at the same delay: no energy reaches the receiver
        var r = Link.QpskLink(Eq() with { EbN0Db = 7, NumSymbols = 600, MultipathDelays = [1, 1], MultipathGains = [[1, 0], [-1, 0]] });
        Assert.Equal(0.5, r.BerTheory);
    }

    [Theory]
    [InlineData("qpsk", 5.0)]
    [InlineData("qam16", 10.0)]
    public void BerBetweenTheBoundAndTheAllowance(string mod, double eb)
    {
        var r = Link.QpskLink(Eq(mod) with { EbN0Db = eb, NumSymbols = 30000, PreambleSymbols = 1000 });
        double eh = 1 + 0.13 + 0.01 + 2 * 0.3 * Rho(0.5, 0.35) - 2 * 0.1 * Rho(1.25, 0.35) - 2 * 0.3 * 0.1 * Rho(0.75, 0.35);
        double low = Theory(mod, eb + 10 * Math.Log10(eh));
        Assert.Equal(low, r.BerTheory!.Value, low * 1e-12);
        double high = Theory(mod, eb + 10 * Math.Log10(eh) - AllowanceDb);
        double sd = Math.Sqrt(high / r.BitErrors.Compared);
        Assert.InRange(r.BitErrors.Rate, low - 4 * sd, high + 4 * sd);
    }

    public static TheoryData<QpskLinkConfig> Rejected() =>
    [
        Eq() with { EqualizerTaps = 0 },
        Eq() with { EqualizerTaps = -1 },
        Eq() with { EqualizerStep = 2.5 },
        Eq() with { EqualizerStep = -0.1 },
        Eq() with { EqualizerStep = double.NaN },
        Eq() with { SamplesPerSymbol = 5 },
        Eq() with { PreambleSymbols = 4000 },
        Eq() with { TimingLoopGains = [0.01, 0] },
        Eq() with { CarrierLoopGains = [0.05, 0.001] },
        Eq("fsk2"),
        Eq("ofdm"),
        Eq() with { EqualizerTaps = null }, // multipath in a single-carrier chain
        new QpskLinkConfig { NumSymbols = 100, EqualizerStep = 3 },
    ];

    [Theory]
    [MemberData(nameof(Rejected))]
    public void Rejects(QpskLinkConfig c) => Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(c));

    [Fact]
    public void ReportJsonCarriesTheEqualizerFields()
    {
        using var doc = System.Text.Json.JsonDocument.Parse(Link.QpskLink(Eq() with { NumSymbols = 600 }).ToJson());
        var config = doc.RootElement.GetProperty("config");
        Assert.Equal(11, config.GetProperty("equalizer_taps").GetInt32());
        Assert.Equal(0.1, config.GetProperty("equalizer_step").GetDouble());
    }
}
