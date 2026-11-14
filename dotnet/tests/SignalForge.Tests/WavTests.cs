using Xunit;

namespace SignalForge.Tests;

/// <summary>WAV files (conventions: Signal files, WAV; ADR 0055).</summary>
public sealed class WavTests : IDisposable
{
    private readonly string _dir = Directory.CreateTempSubdirectory("sfwav").FullName;

    public void Dispose() => Directory.Delete(_dir, true);

    private string PathOf(string name) => Path.Combine(_dir, name);

    [Theory]
    [InlineData("u8", 8, 1)]
    [InlineData("i16", 16, 2)]
    [InlineData("i24", 24, 5)]
    [InlineData("i32", 32, 2)]
    [InlineData("f32", 32, 5)]
    [InlineData("f64", 64, 1)]
    public void RoundTrip(string format, int bits, int nch)
    {
        var rng = new Random(nch);
        double scale = Math.ScaleB(1.0, bits - 1);
        double[][] x = [.. Enumerable.Range(0, nch).Select(_ => Enumerable.Range(0, 101).Select(_ =>
        {
            double v = rng.NextDouble() * 2 - 1;
            return format[0] == 'i' || format == "u8" ? Math.Round(v * (scale - 1)) / scale
                : format == "f32" ? (float)v : v;
        }).ToArray())];
        string path = PathOf("x.wav");
        SignalFiles.WriteWav(path, [.. x.Select(r => new Signal<double>(r, 48000))], format);
        Signal<double>[] got = SignalFiles.ReadWav(path);
        Assert.Equal(nch, got.Length);
        for (int c = 0; c < nch; c++)
        {
            Assert.Equal(x[c], got[c].Samples.ToArray());
            Assert.Equal(48000, got[c].SampleRate);
            Assert.Equal("FS", got[c].Units);
            Assert.Empty(got[c].Metadata);
        }
    }

    [Fact]
    public void OneSignalAndFloatsKeepNonFinite()
    {
        string path = PathOf("x.wav");
        SignalFiles.WriteWav(path, new Signal<double>([double.NaN, double.PositiveInfinity, double.NegativeInfinity, 3.0], 1000));
        double[] s = SignalFiles.ReadWav(path).Single().Samples.ToArray();
        Assert.True(double.IsNaN(s[0]));
        Assert.Equal([double.PositiveInfinity, double.NegativeInfinity, 3.0], s[1..]);
    }

    [Fact]
    public void RejectedWriteLeavesTheFile()
    {
        string path = PathOf("x.wav");
        SignalFiles.WriteWav(path, new Signal<double>([0.5], 1000), "i16");
        byte[] before = File.ReadAllBytes(path);
        Assert.ThrowsAny<ArgumentException>(() => SignalFiles.WriteWav(path, new Signal<double>([1.0], 1000), "i16"));
        Assert.Equal(before, File.ReadAllBytes(path));
    }

    public static TheoryData<Signal<double>[], string> BadWrites() => new()
    {
        { [new([0.0], 1000), new([0.0, 0.0], 1000)], "f32" },
        { [new([0.0], 1000), new([0.0], 2000)], "f32" },
        { [], "f32" },
        { [new([double.NaN], 1000)], "i16" },
        { [new([0.0], 1000.5)], "i16" },
        { [.. Enumerable.Repeat(new Signal<double>([0.0], 1000), 8192)], "f64" },
        { [new([0.0], 1000)], "pcm16" },
    };

    [Theory]
    [MemberData(nameof(BadWrites))]
    public void BadWritesAreRejected(Signal<double>[] channels, string format)
    {
        string path = PathOf("x.wav");
        Assert.ThrowsAny<ArgumentException>(() => SignalFiles.WriteWav(path, channels, format));
        Assert.False(File.Exists(path));
    }

    [Fact]
    public void LargestBlockAlign()
    {
        string path = PathOf("x.wav");
        SignalFiles.WriteWav(path, [.. Enumerable.Repeat(new Signal<double>([0.5], 1), 8191)], "f64"); // 65528 bytes per frame
        Signal<double>[] got = SignalFiles.ReadWav(path);
        Assert.Equal(8191, got.Length);
        Assert.Equal([0.5], got[^1].Samples.ToArray());
    }

    [Fact]
    public void MissingFileIsAnIOError() =>
        Assert.ThrowsAny<IOException>(() => SignalFiles.ReadWav(PathOf("missing.wav")));
}
