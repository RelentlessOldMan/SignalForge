using System.Numerics;
using System.Text.Json;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Signal files: round trips, metadata mapping, write errors (conventions: Signal files).</summary>
public sealed class SignalFilesTests : IDisposable
{
    private readonly string _dir = Directory.CreateTempSubdirectory("signalforge-").FullName;

    public void Dispose() => Directory.Delete(_dir, true);

    private string P(string name) => Path.Combine(_dir, name);

    public static TheoryData<string> Types()
    {
        var t = new TheoryData<string>();
        foreach (char k in "cr")
        {
            foreach (string ty in (string[])["f64", "f32", "i32", "i16"])
            {
                t.Add($"{k}{ty}_le");
                t.Add($"{k}{ty}_be");
            }
            t.Add($"{k}i8");
        }
        return t;
    }

    private static double Step(string datatype) => datatype[1..Math.Min(4, datatype.Length)] switch
    {
        "f64" => 0,
        "f32" => Math.ScaleB(1, -24),
        "i32" => Math.ScaleB(1, -31),
        "i16" => Math.ScaleB(1, -15),
        _ => Math.ScaleB(1, -7),
    };

    [Theory]
    [MemberData(nameof(Types))]
    public void RoundTripEveryDatatype(string datatype)
    {
        var rng = new Random(1);
        double U() => rng.NextDouble() * 1.98 - 0.99;
        if (datatype[0] == 'c')
        {
            Complex[] x = [.. Enumerable.Range(0, 64).Select(_ => new Complex(U(), U()))];
            SignalFiles.WriteSigmf(P("r"), new Signal<Complex>(x, 1e3), datatype);
            var y = SignalFiles.ReadSigmf<Complex>(P("r")).Samples.ToArray();
            Assert.All(x.Zip(y), p => Assert.True(Math.Max(Math.Abs(p.First.Real - p.Second.Real), Math.Abs(p.First.Imaginary - p.Second.Imaginary)) <= Step(datatype)));
            Assert.Equal(SignalFiles.EncodeSamples(x, datatype).Length, new FileInfo(P("r.sigmf-data")).Length);
        }
        else
        {
            double[] x = [.. Enumerable.Range(0, 64).Select(_ => U())];
            SignalFiles.WriteSigmf(P("r"), new Signal<double>(x, 1e3), datatype);
            var y = SignalFiles.ReadSigmf<double>(P("r")).Samples.ToArray();
            Assert.All(x.Zip(y), p => Assert.True(Math.Abs(p.First - p.Second) <= Step(datatype)));
        }
    }

    [Fact]
    public void FieldsAndMetadataRoundTrip()
    {
        var meta = new Dictionary<string, object?>
        {
            ["core:author"] = "me",
            ["run"] = 3,
            ["gains"] = new object[] { 1, 2.5 },
            ["nested"] = new Dictionary<string, object?> { ["a"] = null },
        };
        var s = new Signal<Complex>([new Complex(1, 1), new Complex(0, -0.5)], 2.5e6, 915e6, -1.25, "V", 50, meta);
        SignalFiles.WriteSigmf(P("x.sigmf-meta"), s);
        var r = SignalFiles.ReadSigmf<Complex>(P("x.sigmf-data"));
        Assert.Equal(s.Samples.ToArray(), r.Samples.ToArray());
        Assert.Equal((2.5e6, 915e6, -1.25, "V", (double?)50), (r.SampleRate, r.CenterFrequency, r.TimeOrigin, r.Units, r.Impedance));
        Assert.Equal("me", r.Metadata["core:author"]);
        Assert.Equal(3L, r.Metadata["run"]);
        Assert.Equal([1L, 2.5], (List<object?>)r.Metadata["gains"]!);
        Assert.Null(((Dictionary<string, object?>)r.Metadata["nested"]!)["a"]);
        using var doc = JsonDocument.Parse(File.ReadAllText(P("x.sigmf-meta")));
        var glob = doc.RootElement.GetProperty("global");
        Assert.Equal("cf64_le", glob.GetProperty("core:datatype").GetString());
        Assert.Equal("2500000.0", glob.GetProperty("core:sample_rate").GetRawText());
    }

    [Fact]
    public void EmptySignal()
    {
        SignalFiles.WriteSigmf(P("e"), new Signal<Complex>([], 1), "ci16_le");
        Assert.Equal(0, SignalFiles.ReadSigmf<Complex>(P("e")).Length);
    }

    [Fact]
    public void WrongKindIsRejected()
    {
        SignalFiles.WriteSigmf(P("k"), new Signal<double>([0.5], 1));
        Assert.ThrowsAny<ArgumentException>(() => SignalFiles.ReadSigmf<Complex>(P("k")));
        Assert.ThrowsAny<ArgumentException>(() => SignalFiles.DecodeSamples<float>([0, 0, 0, 0], "rf32_le"));
        Assert.ThrowsAny<ArgumentException>(() => SignalFiles.WriteSigmf(P("k"), new Signal<double>([0.5], 1), "cf32_le"));
    }

    [Theory]
    [InlineData("core:sample_rate", 2)]
    [InlineData("signalforge:x", 1)]
    [InlineData("bad", double.NaN)]
    public void WriteRejectsBadMetadata(string key, object value) =>
        Assert.ThrowsAny<ArgumentException>(() =>
            SignalFiles.WriteSigmf(P("w"), new Signal<double>([0.5], 1, metadata: new Dictionary<string, object?> { [key] = value })));

    [Fact]
    public void WriteRejectsNonJsonAndNonFinite()
    {
        Assert.ThrowsAny<ArgumentException>(() =>
            SignalFiles.WriteSigmf(P("w"), new Signal<double>([0.5], 1, metadata: new Dictionary<string, object?> { ["o"] = new object() })));
        Assert.ThrowsAny<ArgumentException>(() => SignalFiles.WriteSigmf(P("w"), new Signal<double>([0.5], 1, double.PositiveInfinity)));
        Assert.ThrowsAny<ArgumentException>(() => SignalFiles.WriteSigmf(P("w"), new Signal<double>([0.5], 1, 0, double.NaN)));
    }

    [Fact]
    public void MissingFileIsAnIoError() =>
        Assert.Throws<FileNotFoundException>(() => SignalFiles.ReadSigmf<double>(P("absent")));

    private static object Nest(int k)
    {
        object v = new List<object?>();
        for (int i = 1; i < k; i++)
            v = new List<object?> { v };
        return v;
    }

    [Theory]
    [InlineData("plain", 61)]
    [InlineData("x:colon", 62)]
    public void MetadataNestingLimit(string key, int fits)
    {
        // A plain key's value sits at level 4 (document, global, signalforge:metadata), a colon key's
        // at level 3; 64 levels in all is the limit, read and write.
        SignalFiles.WriteSigmf(P("ok"), new Signal<double>([0.5], 1, metadata: new Dictionary<string, object?> { [key] = Nest(fits) }));
        object? back = SignalFiles.ReadSigmf<double>(P("ok")).Metadata[key];
        for (int i = 1; i < fits; i++)
            back = Assert.Single(Assert.IsType<List<object?>>(back));
        Assert.Empty(Assert.IsType<List<object?>>(back));
        var e = Assert.ThrowsAny<ArgumentException>(() =>
            SignalFiles.WriteSigmf(P("deep"), new Signal<double>([0.5], 1, metadata: new Dictionary<string, object?> { [key] = Nest(fits + 1) })));
        Assert.Contains("deeper", e.Message, StringComparison.Ordinal);
        File.WriteAllText(P("deep.sigmf-meta"), File.ReadAllText(P("ok.sigmf-meta")).Replace("[]", "[[]]", StringComparison.Ordinal));
        File.Copy(P("ok.sigmf-data"), P("deep.sigmf-data"));
        Assert.ThrowsAny<ArgumentException>(() => SignalFiles.ReadSigmf<double>(P("deep")));
    }

    [Fact]
    public void AFailedWriteLeavesExistingFiles()
    {
        SignalFiles.WriteSigmf(P("r"), new Signal<double>([0.25], 1));
        byte[][] before = [File.ReadAllBytes(P("r.sigmf-meta")), File.ReadAllBytes(P("r.sigmf-data"))];
        foreach (object bad in (object[])["a\ud800b", ulong.MaxValue, (ulong)long.MaxValue + 1])
            Assert.ThrowsAny<ArgumentException>(() =>
                SignalFiles.WriteSigmf(P("r"), new Signal<double>([0.5, 0.5], 2, metadata: new Dictionary<string, object?> { ["n"] = bad })));
        Assert.ThrowsAny<ArgumentException>(() => SignalFiles.WriteSigmf(P("r"), new Signal<double>([0.5], 2, units: "\udc00")));
        Assert.Equal(before[0], File.ReadAllBytes(P("r.sigmf-meta")));
        Assert.Equal(before[1], File.ReadAllBytes(P("r.sigmf-data")));
    }

    [Fact]
    public void Int64ExtremesRoundTrip()
    {
        SignalFiles.WriteSigmf(P("r"), new Signal<double>([0.5], 1, metadata: new Dictionary<string, object?> { ["lo"] = long.MinValue, ["hi"] = (ulong)long.MaxValue }));
        var m = SignalFiles.ReadSigmf<double>(P("r")).Metadata;
        Assert.Equal(long.MinValue, m["lo"]);
        Assert.Equal(long.MaxValue, m["hi"]);
    }
}
