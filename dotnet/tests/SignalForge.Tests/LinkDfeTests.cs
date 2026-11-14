using Xunit;

namespace SignalForge.Tests;

/// <summary>Decision feedback and the preamble frequency in the link (conventions: QPSK link,
/// Receiver, step 7; ADR 0070).</summary>
public sealed class LinkDfeTests
{
    // an echo of 0.9 one symbol late: a notch 20 dB deep at half the symbol rate
    private static readonly int[] Delays = [0, 4];
    private static readonly double[][] Gains = [[1, 0], [0.9, 0]];

    private static QpskLinkConfig Dfe(string modulation = "qpsk") => new()
    {
        Modulation = modulation,
        NumSymbols = 4000,
        PreambleSymbols = 1000,
        DelaySamples = 3,
        FrequencyOffsetHz = 5,
        Phase = 0.7,
        EqualizerTaps = 11,
        EqualizerFeedback = 2,
        MultipathDelays = Delays,
        MultipathGains = Gains,
    };

    private static QpskLinkConfig Flat(QpskLinkConfig c) => c with { MultipathDelays = null, MultipathGains = null };

    [Theory]
    [InlineData("qpsk", 1000)]
    [InlineData("qam16", 1000)]
    [InlineData("psk8", 1000)]
    [InlineData("qam64", 2000)] // its decisions need the taps nearer convergence than 1000 symbols leave
    public void NoiselessEchoIsRecoveredWithFeedback(string mod, int pre)
    {
        var r = Link.QpskLink(Dfe(mod) with { PreambleSymbols = pre });
        Assert.Equal(0, r.BitErrors.Errors);
        Assert.True(r.Evm!.Rms < 0.08);
    }

    [Theory]
    [InlineData("qam16")]
    [InlineData("psk8")]
    [InlineData("qam64")]
    public void TheLinearEqualizerCannotSpanTheEcho(string mod) =>
        // its inverse decays as 0.9^k, longer than 11 taps at half a symbol reach
        Assert.True(Link.QpskLink(Dfe(mod) with { EqualizerFeedback = 0 }).BitErrors.Errors > 0);

    [Fact]
    public void PreambleFrequencyThroughTheEcho()
    {
        // the blind QPSK estimate is about 1 Hz off through this echo at 8 dB (ADR 0070)
        for (int seed = 0; seed < 5; seed++)
        {
            var r = Link.QpskLink(Dfe() with { EbN0Db = 8, Seed = seed });
            Assert.InRange(r.FrequencyOffsetHz!.Value, 4.9, 5.1); // a test allowance, not derived
        }
    }

    [Fact]
    public void NoiselessFlatPreambleFrequency()
    {
        var with = Link.QpskLink(Flat(Dfe()) with { EqualizerFeedback = 0 });
        var without = Link.QpskLink(Flat(Dfe()) with { EqualizerTaps = null, EqualizerFeedback = 0 });
        Assert.Equal(5, with.FrequencyOffsetHz!.Value, 1e-3);
        Assert.Equal(without.TimingOffset, with.TimingOffset);
        Assert.Equal(without.FrameStart, with.FrameStart);
        Assert.Equal(without.PhaseOffset!.Value, with.PhaseOffset!.Value, 1e-6); // f₁ differs (ADR 0071)
    }

    [Fact]
    public void FewerThanTwoFullBlocksKeepTheChainFrequency() =>
        // P = 40 and B = 32 leave one full block: steps 2-6 give the frequency, from the data-aided f1
        Assert.Equal(5, Link.QpskLink(Flat(Dfe()) with { PreambleSymbols = 40 }).FrequencyOffsetHz!.Value, 1e-5); // a test allowance

    [Fact]
    public void OnePreambleSymbolKeepsTheBlindEstimate()
    {
        // no symbol-to-symbol step to correlate: f1 is the blind estimate (ADR 0071)
        var c = Flat(Dfe()) with { PreambleSymbols = 1 };
        Assert.Equal(Link.QpskLink(c with { EqualizerTaps = null, EqualizerFeedback = 0 }).FrequencyOffsetHz,
            Link.QpskLink(c).FrequencyOffsetHz);
    }

    [Theory]
    [InlineData(71, 5.0)]
    [InlineData(72, 37.0)]
    [InlineData(73, -120.0)]
    public void DataAidedCoarseFrequencyFor8Psk(int seed, double f0)
    {
        // the 8th-power estimate is 31.25 Hz off here without the preamble (ADR 0071)
        var r = Link.QpskLink(Dfe("psk8") with { EbN0Db = 12, NumSymbols = 20000, Seed = seed, FrequencyOffsetHz = f0 });
        Assert.InRange(r.FrequencyOffsetHz!.Value, f0 - 0.05, f0 + 0.05); // a test allowance, not derived
        Assert.True(r.BitErrors.Rate < 0.002); // measured 0.0002-0.0011 over four seeds (ADR 0071)
    }

    [Theory]
    [InlineData("qpsk", 8.0)]
    [InlineData("qam16", 14.0)]
    public void FeedbackBeatsTheLinearEqualizerAboveTheBound(string mod, double eb)
    {
        var c = Dfe(mod) with { EbN0Db = eb, NumSymbols = 20000, Seed = 70 };
        var dfe = Link.QpskLink(c);
        var lms = Link.QpskLink(c with { EqualizerFeedback = 0 });
        double ebEff = eb + 10 * Math.Log10(1 + 0.81); // paths a whole symbol apart: rho(1) = 0, so the energies add
        double bound = mod == "qpsk" ? Metrics.QpskBerTheory(ebEff) : Metrics.Qam16BerTheory(ebEff);
        Assert.Equal(bound, dfe.BerTheory!.Value, bound * 1e-12);
        Assert.InRange(dfe.BitErrors.Rate, bound, lms.BitErrors.Rate / 10);
    }

    public static TheoryData<QpskLinkConfig> Rejected() =>
    [
        Dfe() with { EqualizerFeedback = -1 },
        Flat(Dfe()) with { EqualizerTaps = null },
    ];

    [Theory]
    [MemberData(nameof(Rejected))]
    public void Rejects(QpskLinkConfig c) => Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(c));

    [Fact]
    public void ReportJsonCarriesTheFeedbackCount()
    {
        using var doc = System.Text.Json.JsonDocument.Parse(Link.QpskLink(Dfe() with { NumSymbols = 1200 }).ToJson());
        Assert.Equal(2, doc.RootElement.GetProperty("config").GetProperty("equalizer_feedback").GetInt32());
    }
}
