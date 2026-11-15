using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>2-D members of NumPy .npz archives (conventions: Signal files, NumPy .npz; ADR 0093).</summary>
public sealed class Npz2DTests : IDisposable
{
    private static readonly double[] Taps = [0.5, -0.25, 0.125];
    private readonly string _dir = Directory.CreateTempSubdirectory("sfnpz2d").FullName;

    public void Dispose() => Directory.Delete(_dir, true);

    private string PathOf(string name) => Path.Combine(_dir, name);

    private static KeyValuePair<string, Array>[] Mixed() =>
    [
        new("taps", Taps),
        new("bank", new double[,] { { 1, 2, 3 }, { 4, 5, double.NaN } }),
        new("iq", new Complex[,] { { new(1, 2), new(0, -1) }, { new(double.PositiveInfinity, 0), Complex.Zero } }),
        new("none", new double[0, 3]),
        new("thin", new Complex[4, 0]),
    ];

    [Fact]
    public void RoundTripKeepsEachMembersDimensions()
    {
        SignalFiles.WriteNpz(PathOf("m.npz"), Mixed());
        var got = SignalFiles.ReadNpz(PathOf("m.npz"));
        Assert.Equal(Mixed().Select(kv => kv.Key), got.Keys);
        foreach ((string key, Array want) in Mixed())
        {
            Assert.IsType(want.GetType(), got[key]);
            Assert.Equal(want.Rank, got[key].Rank);
            for (int d = 0; d < want.Rank; d++)
                Assert.Equal(want.GetLength(d), got[key].GetLength(d));
            Assert.Equal(want.Cast<object>(), got[key].Cast<object>());
        }
    }

    [Fact]
    public void MembersAreTheWriteNpyBytes()
    {
        var bank = new double[,] { { 1, 2, 3 }, { 4, 5, 6 } };
        SignalFiles.WriteNpz(PathOf("a.npz"), [new("bank", bank)]);
        SignalFiles.WriteNpy(PathOf("bank.npy"), bank);
        byte[] archive = File.ReadAllBytes(PathOf("a.npz")), npy = File.ReadAllBytes(PathOf("bank.npy"));
        Assert.True(archive.AsSpan().IndexOf(npy) > 0);
    }

    [Fact]
    public void OtherElementTypesAreRejected()
    {
        var e = Assert.Throws<ArgumentException>(() => SignalFiles.WriteNpz(PathOf("b.npz"), [new("x", new float[1, 1])]));
        Assert.Contains("double[,]", e.Message, StringComparison.Ordinal);
        Assert.Throws<ArgumentException>(() => SignalFiles.WriteNpz(PathOf("b.npz"), [new("x", new double[1, 1, 1])]));
    }
}
