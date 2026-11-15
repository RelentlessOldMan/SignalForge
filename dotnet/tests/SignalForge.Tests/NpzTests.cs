using System.Buffers.Binary;
using System.IO.Compression;
using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>NumPy .npz archives (conventions: Signal files, NumPy .npz; ADR 0089).</summary>
public sealed class NpzTests : IDisposable
{
    private static readonly double[] One = [1.0], Two = [2.0], OneTwo = [1.0, 2.0];
    private static readonly float[] SingleOne = [1f];

    private readonly string _dir = Directory.CreateTempSubdirectory("sfnpz").FullName;

    public void Dispose() => Directory.Delete(_dir, true);

    private string PathOf(string name) => Path.Combine(_dir, name);

    private static KeyValuePair<string, Array>[] Arrays() =>
    [
        new("taps", new[] { 0.5, -0.25, double.NaN, double.PositiveInfinity }),
        new("iq", new Complex[] { new(1, 2), new(double.NegativeInfinity, 0), new(0, -0.5) }),
        new("empty", Array.Empty<double>()),
        new("big", Enumerable.Range(0, 100000).Select(k => (double)k).ToArray()),
    ];

    [Fact]
    public void RoundTripKeepsOrderAndType()
    {
        string path = PathOf("a.npz");
        SignalFiles.WriteNpz(path, Arrays());
        var got = SignalFiles.ReadNpz(path);
        Assert.Equal(Arrays().Select(kv => kv.Key), got.Keys);
        foreach (var (key, want) in Arrays())
            Assert.Equal(want, got[key]);
    }

    [Fact]
    public void ZipArchiveReadsWhatWeWriteAsStoredMembers()
    {
        string path = PathOf("a.npz");
        SignalFiles.WriteNpz(path, Arrays());
        using var zip = ZipFile.OpenRead(path);
        Assert.Equal(["taps.npy", "iq.npy", "empty.npy", "big.npy"], zip.Entries.Select(e => e.FullName));
        foreach (var e in zip.Entries)
        {
            Assert.Equal(e.Length, e.CompressedLength);
            string npy = PathOf(e.FullName);
            e.ExtractToFile(npy);
            Assert.Equal(File.ReadAllBytes(npy), Member(path, e.FullName));
        }
        string one = PathOf("one.npy");
        SignalFiles.WriteNpy(one, new[] { 0.5, -0.25, double.NaN, double.PositiveInfinity });
        Assert.Equal(File.ReadAllBytes(one), File.ReadAllBytes(PathOf("taps.npy")));
    }

    [Theory]
    [InlineData(CompressionLevel.NoCompression)]
    [InlineData(CompressionLevel.Fastest)]
    [InlineData(CompressionLevel.SmallestSize)]
    public void ReadsZipArchiveOutput(CompressionLevel level)
    {
        string path = PathOf("a.npz");
        using (var zip = ZipFile.Open(path, ZipArchiveMode.Create))
        {
            foreach (var (key, x) in Arrays())
            {
                string npy = PathOf(key + ".npy");
                if (x is Complex[] z)
                    SignalFiles.WriteNpy(npy, z);
                else
                    SignalFiles.WriteNpy(npy, (double[])x);
                zip.CreateEntryFromFile(npy, key + ".npy", level);
            }
        }
        var got = SignalFiles.ReadNpz(path);
        foreach (var (key, want) in Arrays())
            Assert.Equal(want, got[key]);
    }

    [Fact]
    public void EmptyArchiveIsTheEndRecordAlone()
    {
        string path = PathOf("a.npz");
        SignalFiles.WriteNpz(path, []);
        Assert.Equal([0x50, 0x4B, 5, 6, .. new byte[18]], File.ReadAllBytes(path));
        Assert.Empty(SignalFiles.ReadNpz(path));
    }

    [Theory]
    [InlineData("")]
    [InlineData("a/b")]
    [InlineData("a\\b")]
    [InlineData("é")]
    [InlineData("tab\there")]
    [InlineData("nul\0")]
    [InlineData("\u007f")]
    public void BadNamesAreRejected(string name) =>
        Assert.ThrowsAny<ArgumentException>(() =>
            SignalFiles.WriteNpz(PathOf("a.npz"), [new(name, One)]));

    [Fact]
    public void BadArgumentsAreRejected()
    {
        Assert.ThrowsAny<ArgumentException>(() =>
            SignalFiles.WriteNpz(PathOf("a.npz"), [new(new string('n', 251), One)]));
        Assert.ThrowsAny<ArgumentException>(() =>
            SignalFiles.WriteNpz(PathOf("a.npz"), [new("x", One), new("x", Two)]));
        Assert.ThrowsAny<ArgumentException>(() =>
            SignalFiles.WriteNpz(PathOf("a.npz"), [new("x", SingleOne)]));
        Assert.ThrowsAny<ArgumentException>(() => SignalFiles.WriteNpz(PathOf("a.npz"), null!));
    }

    [Fact]
    public void EachFlippedCrcBitIsCaught()
    {
        string path = PathOf("a.npz");
        SignalFiles.WriteNpz(path, [new("x", OneTwo)]);
        byte[] good = File.ReadAllBytes(path);
        int at = IndexOf(good, [0x50, 0x4B, 1, 2]) + 16;
        uint crc = BinaryPrimitives.ReadUInt32LittleEndian(good.AsSpan(at));
        for (int bit = 0; bit < 32; bit++)
        {
            byte[] bad = (byte[])good.Clone();
            BinaryPrimitives.WriteUInt32LittleEndian(bad.AsSpan(at), crc ^ (1u << bit));
            File.WriteAllBytes(path, bad);
            var e = Assert.ThrowsAny<ArgumentException>(() => SignalFiles.ReadNpz(path));
            Assert.Contains("CRC", e.Message, StringComparison.Ordinal);
        }
    }

    private static byte[] Member(string path, string name)
    {
        using var zip = ZipFile.OpenRead(path);
        using var s = zip.GetEntry(name)!.Open();
        using var m = new MemoryStream();
        s.CopyTo(m);
        return m.ToArray();
    }

    private static int IndexOf(byte[] haystack, byte[] needle) => haystack.AsSpan().IndexOf(needle);
}
