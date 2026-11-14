using Xunit;

namespace SignalForge.Tests;

/// <summary>Phase noise and clock offset in the OFDM link (conventions: QPSK link, OFDM; ADR 0065).</summary>
public sealed class OfdmImpairmentTests
{
    private const int U = 52;
    private static readonly int[] Guarded = [.. Enumerable.Range(-26, 53).Where(k => k != 0)]; // resampling cannot keep the band edge
    private static readonly double[] Loop = [0.3, 0.02];
    private const double AllowanceDb = 0.5; // leakage between subcarriers and loop jitter: a test allowance, not derived

    private static QpskLinkConfig Ofdm() => new()
    {
        Modulation = "ofdm",
        NumSymbols = U * 400,
        PreambleSymbols = U * 16,
        OfdmSubcarriers = Guarded,
        DelaySamples = 11,
        FrequencyOffsetHz = -20,
    };

    [Theory]
    [InlineData(200.0)]
    [InlineData(-200.0)]
    public void NoiselessClockOffsetNeedsTheLoop(double ppm)
    {
        var r = Link.QpskLink(Ofdm() with { ClockOffsetPpm = ppm, TimingLoopGains = Loop });
        Assert.Equal(0, r.BitErrors.Errors);
        Assert.True(r.Evm!.Rms < 0.05);
        var off = Link.QpskLink(Ofdm() with { ClockOffsetPpm = ppm });
        Assert.True(off.BitErrors.Rate > 0.1);
    }

    public static TheoryData<QpskLinkConfig> Within() =>
    [
        Ofdm() with { ClockOffsetPpm = -150, TimingLoopGains = Loop },
        Ofdm() with { PhaseNoiseLinewidthHz = 0.1 },
        Ofdm() with { TimingLoopGains = Loop }, // the loop on a clean clock
    ];

    [Theory]
    [MemberData(nameof(Within))]
    public void BerWithinTheAllowance(QpskLinkConfig c)
    {
        const double eb = 6;
        const int p = 16;
        long errors = 0, compared = 0;
        for (int seed = 0; seed < 3; seed++)
        {
            var r = Link.QpskLink(c with { EbN0Db = eb, Seed = seed });
            Assert.Equal(Metrics.QpskBerTheory(eb), r.BerTheory);
            errors += r.BitErrors.Errors;
            compared += r.BitErrors.Compared;
        }
        double low = Metrics.QpskBerTheory(eb), high = Metrics.QpskBerTheory(eb - 10 * Math.Log10(1 + 1.0 / p) - AllowanceDb);
        double ber = (double)errors / compared, sd = Math.Sqrt(high / compared);
        Assert.InRange(ber, low - 4 * sd, high + 4 * sd);
    }

    [Fact]
    public void PhaseNoiseNoiseless() =>
        Assert.Equal(0, Link.QpskLink(Ofdm() with { PhaseNoiseLinewidthHz = 0.1, Seed = 4 }).BitErrors.Errors);

    [Fact]
    public void ALongPreambleKeepsItsPhase()
    {
        // 200 preamble blocks with the prefix's frequency error: each block is turned to block 0's
        // phase before the average, so the estimate does not smear (ADR 0065)
        var r = Link.QpskLink(new QpskLinkConfig
        {
            Modulation = "ofdm",
            NumSymbols = 63 * 200,
            PreambleSymbols = 63 * 200,
            EbN0Db = 10,
            Seed = 2,
        });
        Assert.Equal(1.0 / 20, r.Evm!.Rms * r.Evm.Rms, 0.05 / 20);
    }

    public static TheoryData<QpskLinkConfig> Bad() =>
    [
        Ofdm() with { ClockOffsetPpm = 300 }, // 300e-6 * (11 + 400 * 80) > 8
        Ofdm() with { ClockOffsetPpm = 1, MultipathDelays = [8], MultipathGains = [[1, 0]] },
        Ofdm() with { CarrierLoopGains = [0.01, 0] },
        Ofdm() with { ClockOffsetPpm = 250 }, // 8.00275 > 8
    ];

    [Theory]
    [MemberData(nameof(Bad))]
    public void Rejects(QpskLinkConfig c) => Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(c));

    [Fact]
    public void DriftAtTheMarginIsAccepted() =>
        Assert.Equal(0, Link.QpskLink(Ofdm() with { ClockOffsetPpm = -249, TimingLoopGains = Loop }).BitErrors.Errors);
}
