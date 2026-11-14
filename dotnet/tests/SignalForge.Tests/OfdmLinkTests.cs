using Xunit;

namespace SignalForge.Tests;

/// <summary>OFDM in the link (conventions: QPSK link, OFDM; ADR 0063).</summary>
public sealed class OfdmLinkTests
{
    private const double Fs = 4000; // default SymbolRate times SamplesPerSymbol
    private const int U = 63; // default subcarriers: all 64 but DC

    private static QpskLinkConfig Ofdm() => new() { NumSymbols = U * 20, PreambleSymbols = U, Modulation = "ofdm" };

    [Theory]
    [InlineData(0, 0.0, 0.0)]
    [InlineData(37, 7.3, 1.1)]
    [InlineData(5, -30.0, -2.5)]
    [InlineData(130, 29.0, 3.0)]
    public void NoiselessRecoversEverything(int delay, double f, double phase)
    {
        var r = Link.QpskLink(Ofdm() with { DelaySamples = delay, FrequencyOffsetHz = f, Phase = phase });
        Assert.Equal((delay / 4, (double)(delay % 4)), (r.FrameStart, r.TimingOffset));
        Assert.Equal(f, r.FrequencyOffsetHz!.Value, 1e-9);
        double want = phase + 2 * Math.PI * f * delay / Fs;
        Assert.True(Math.Abs(Math.IEEERemainder(r.PhaseOffset!.Value - want, 2 * Math.PI)) < 1e-9);
        Assert.True(r.Evm!.Rms < 1e-12);
        Assert.Equal((0, 2 * U * 20), (r.BitErrors.Errors, r.BitErrors.Compared));
        Assert.Null(r.BerTheory);
    }

    [Fact]
    public void OneBlockAndAShortPrefix()
    {
        var r = Link.QpskLink(Ofdm() with
        {
            NumSymbols = 4,
            PreambleSymbols = 4,
            OfdmNfft = 8,
            OfdmCpLen = 1,
            OfdmSubcarriers = [-3, -1, 2, 3],
            DelaySamples = 3,
        });
        Assert.Equal((0, 3.0, 0), (r.FrameStart, r.TimingOffset, r.BitErrors.Errors));
    }

    [Fact]
    public void BerBetweenKnownChannelAndEstimateLoss()
    {
        const int p = 8;
        const double eb = 6;
        long errors = 0, compared = 0;
        double? theory = null;
        for (int seed = 0; seed < 4; seed++)
        {
            var r = Link.QpskLink(Ofdm() with
            {
                NumSymbols = U * 200,
                PreambleSymbols = U * p,
                EbN0Db = eb,
                Seed = seed,
                FrequencyOffsetHz = -20,
                Phase = 0.3,
                DelaySamples = 11,
            });
            Assert.Equal(2, r.FrameStart);
            errors += r.BitErrors.Errors;
            compared += r.BitErrors.Compared;
            theory = r.BerTheory;
        }
        double low = Metrics.QpskBerTheory(eb), high = Metrics.QpskBerTheory(eb - 10 * Math.Log10(1 + 1.0 / p));
        Assert.Equal(low, theory);
        double ber = (double)errors / compared, sd = Math.Sqrt(high / compared);
        Assert.InRange(ber, low - 4 * sd, high + 4 * sd);
    }

    [Fact]
    public void NoiseIsPerDataSubcarrier()
    {
        const double eb = 10;
        var r = Link.QpskLink(Ofdm() with { NumSymbols = U * 200, PreambleSymbols = U * 200, EbN0Db = eb });
        double n0 = 1 / (2 * Math.Pow(10, eb / 10));
        Assert.Equal(1, r.Evm!.Rms * r.Evm.Rms / n0, 0.05);
    }

    public static TheoryData<QpskLinkConfig> Bad() =>
    [
        Ofdm() with { NumSymbols = U * 20 + 1 },
        Ofdm() with { PreambleSymbols = U + 1 },
        Ofdm() with { OfdmNfft = 1 },
        Ofdm() with { OfdmCpLen = 0 },
        Ofdm() with { OfdmCpLen = 65 },
        Ofdm() with { OfdmSubcarriers = [] },
        Ofdm() with { OfdmSubcarriers = [1, 1], NumSymbols = 2, PreambleSymbols = 2 },
        Ofdm() with { OfdmSubcarriers = [32] },
        Ofdm() with { FrequencyOffsetHz = 31.25 },
        Ofdm() with { PhaseNoiseLinewidthHz = 1 },
        Ofdm() with { ClockOffsetPpm = 10 },
        Ofdm() with { TimingLoopGains = [0.01, 0] },
        Ofdm() with { CarrierLoopGains = [0.01, 0] },
        Ofdm() with { Rolloff = 2 },
        new() { NumSymbols = 64, OfdmCpLen = 0 },
    ];

    [Theory]
    [MemberData(nameof(Bad))]
    public void Rejects(QpskLinkConfig c) => Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(c));

    [Fact]
    public void SubcarriersAreReported()
    {
        var r = Link.QpskLink(new QpskLinkConfig { NumSymbols = 64, OfdmSubcarriers = [3, -2] });
        Assert.Contains("\"ofdm_subcarriers\": [\n      3,\n      -2\n    ]", r.ToJson().Replace("\r\n", "\n", StringComparison.Ordinal), StringComparison.Ordinal);
    }
}
