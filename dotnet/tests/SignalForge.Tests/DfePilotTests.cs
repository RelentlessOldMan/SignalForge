using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Pilots that correct the equalizer phase loop's cycle slips (conventions:
/// Synchronization, Decision-feedback equalizer; ADR 0075).</summary>
public sealed class DfePilotTests
{
    private static Complex[] Psk8(int seed, int n)
    {
        var rng = new Random(seed);
        var bits = new byte[3 * n];
        for (int i = 0; i < bits.Length; i++)
            bits[i] = (byte)rng.Next(2);
        return Modulation.Psk8Map(bits);
    }

    // an exact pi/4 turn from symbol `at` on: 8-PSK decides it as other points with no error
    private static Complex[] Jump(Complex[] a, int at) =>
        [.. a.Select((z, k) => k >= at ? z * Complex.FromPolarCoordinates(1, Math.PI / 4) : z)];

    private static Complex[] Every(Complex[] a, int first, int step) =>
        [.. Enumerable.Range(0, (a.Length - first + step - 1) / step).Select(j => a[first + j * step])];

    private static bool Close(Complex[] y, Complex[] a, int from, int to, double tol)
    {
        for (int k = from; k < to; k++)
            if ((y[k] - a[k]).Magnitude > tol)
                return false;
        return true;
    }

    [Fact]
    public void PilotsUndoASlipAfterTheWindow()
    {
        Complex[] a = Psk8(5, 60), x = Jump(a, 10), pilots = Every(a, 14, 5);
        DfeEqualization plain = Sync.DfeEqualizer(x, a.AsSpan(0, 10), 1, 0, 0, decision: "psk8", phaseLoopGains: (0, 0));
        Assert.True(Close(plain.Symbols, x, 10, 60, 1e-15)); // nothing sees the turn
        DfeEqualization r = Sync.DfeEqualizer(x, a.AsSpan(0, 10), 1, 0, 0, decision: "psk8", phaseLoopGains: (0, 0),
            pilots: pilots, pilotInterval: 5);
        // window 2: corrected after the second pilot, output 19
        Assert.True(Close(r.Symbols, x, 0, 20, 1e-15));
        Assert.True(Close(r.Symbols, a, 20, 60, 1e-14));
        DfeEqualization r1 = Sync.DfeEqualizer(x, a.AsSpan(0, 10), 1, 0, 0, decision: "psk8", phaseLoopGains: (0, 0),
            pilots: pilots, pilotInterval: 5, slipWindow: 1);
        Assert.True(Close(r1.Symbols, a, 15, 60, 1e-14));
    }

    [Fact]
    public void APilotIsTheReferenceThere()
    {
        Complex[] a = Psk8(6, 40), x = Jump(a, 8);
        DfeEqualization r = Sync.DfeEqualizer(x, a.AsSpan(0, 8), 1, 0, 0, decision: "psk8", phaseLoopGains: (0, 0),
            pilots: Every(a, 10, 3), pilotInterval: 3, slipWindow: 100);
        // with no correction yet, the error at a pilot is against the pilot, not the decision
        Assert.True((r.Errors[10] - (a[10] - x[10])).Magnitude < 1e-15);
        Assert.True(r.Errors[9].Magnitude < 1e-15);
    }

    [Fact]
    public void Rejects()
    {
        Complex[] x = [1, Complex.ImaginaryOne, -1, -Complex.ImaginaryOne];
        Complex[] t = [1], three = [1, Complex.ImaginaryOne, -1];
        DfeEqualization Run(Complex[]? p, int? k, int w = 2, (double, double)? g = null) =>
            Sync.DfeEqualizer(x, t, 3, 0, 0.5, decision: "qpsk", phaseLoopGains: g ?? (0.1, 0), pilots: p, pilotInterval: k,
                slipWindow: w);
        Assert.ThrowsAny<ArgumentException>(() => Run(three, null));
        Assert.ThrowsAny<ArgumentException>(() => Run(null, 1));
        Assert.ThrowsAny<ArgumentException>(() => Run([1, Complex.ImaginaryOne], 1));
        Assert.ThrowsAny<ArgumentException>(() => Run(three, 0));
        Assert.ThrowsAny<ArgumentException>(() => Run(three, 1, 0));
        Assert.ThrowsAny<ArgumentException>(() => Run([1, double.NaN, -1], 1));
        Assert.ThrowsAny<ArgumentException>(() =>
            Sync.DfeEqualizer(x, t, 3, 0, 0.5, decision: "qpsk", pilots: three, pilotInterval: 1));
    }

    private static readonly int[] Delays = [0, 4];
    private static readonly double[][] Gains = [[1, 0], [0.9, 0]];

    private static QpskLinkConfig Psk8Link(int seed) => new()
    {
        Modulation = "psk8",
        NumSymbols = 6000,
        PreambleSymbols = 100,
        EbN0Db = 12,
        FrequencyOffsetHz = 5,
        EqualizerTaps = 11,
        EqualizerFeedback = 2,
        EqualizerStart = "least_squares",
        EqualizerLoopGains = [0.01, 0.0001],
        PilotInterval = 20,
        Seed = seed,
        MultipathDelays = Delays,
        MultipathGains = Gains,
    };

    [Fact]
    public void LinkPilotsCatchTheSlips()
    {
        // measured in ADR 0075 (Python's noise): 0.0012-0.0099 with pilots; 6 of 10 slip without
        double[] with = [.. Enumerable.Range(80, 10).Select(s => Link.QpskLink(Psk8Link(s)).BitErrors.Rate)];
        double[] without = [.. Enumerable.Range(80, 10).Select(s => Link.QpskLink(Psk8Link(s) with { PilotInterval = null }).BitErrors.Rate)];
        Assert.True(with.Max() < 0.015, string.Join(", ", with));
        Assert.True(without.Max() > 0.1, string.Join(", ", without));
    }

    [Fact]
    public void LinkPilotsDoNotCount()
    {
        QpskLinkConfig c = Psk8Link(80) with { Modulation = "qpsk", EbN0Db = null, NumSymbols = 1000, PilotInterval = 7 };
        ErrorCount e = Link.QpskLink(c).BitErrors;
        Assert.Equal(2 * (1000 - 100 - (900 / 7)), e.Compared);
        Assert.True(e.Rate < 0.01); // the loop settling in, not the pilots
        Assert.Equal(2 * 900, Link.QpskLink(c with { PilotInterval = null }).BitErrors.Compared);
    }

    [Fact]
    public void LinkRejects()
    {
        Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(Psk8Link(80) with { PilotInterval = 0 }));
        Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(Psk8Link(80) with { EqualizerLoopGains = null }));
    }
}
