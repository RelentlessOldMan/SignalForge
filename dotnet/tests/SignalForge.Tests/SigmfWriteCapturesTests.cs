using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Writing multi-capture SigMF recordings (conventions: Signal files, Captures; ADR 0100).</summary>
public sealed class SigmfWriteCapturesTests : IDisposable
{
    private const string ByHand = """
        {
          "global": {
            "core:datatype": "rf64_le",
            "core:version": "1.2.0",
            "core:sample_rate": 4.0,
            "core:extensions": [
              {
                "name": "signalforge",
                "version": "1.0.0",
                "optional": true
              }
            ],
            "signalforge:time_origin": 0.5,
            "signalforge:metadata": {
              "k": 1
            }
          },
          "captures": [
            {
              "core:sample_start": 0,
              "core:frequency": 100.0
            },
            {
              "core:sample_start": 3,
              "core:frequency": 200.0
            }
          ],
          "annotations": [
            {
              "core:sample_start": 2,
              "core:label": "x"
            },
            {
              "core:sample_start": 3,
              "core:sample_count": 5
            }
          ]
        }

        """;

    private readonly string _dir = Directory.CreateTempSubdirectory("signalforge-").FullName;

    public void Dispose() => Directory.Delete(_dir, true);

    private string P(string name) => Path.Combine(_dir, name);

    private static Dictionary<string, object?> At(long start, params (string Key, object? Value)[] more)
    {
        var a = new Dictionary<string, object?> { ["core:sample_start"] = start };
        foreach (var (k, v) in more)
            a[k] = v;
        return a;
    }

    private static Signal<T> Seg<T>(T[] x, double t0, double f = 0, Dictionary<string, object?>[]? ann = null, double rate = 4)
        where T : struct
    {
        var md = new Dictionary<string, object?> { ["k"] = 1L };
        if (ann is not null)
            md["core:annotations"] = ann.Cast<object?>().ToList();
        return new Signal<T>(x, rate, f, t0, metadata: md);
    }

    private void SameFiles(string a, string b)
    {
        foreach (string ext in new[] { ".sigmf-meta", ".sigmf-data" })
            Assert.Equal(File.ReadAllBytes(P(a + ext)), File.ReadAllBytes(P(b + ext)));
    }

    [Fact]
    public void WritesTheFilesByHand()
    {
        var a = Seg([1.0, 2, 3], 0.5, 100, [At(2, ("core:label", "x"))]);
        var b = Seg([4.0], 0.5 + 3 / 4.0, 200, [At(0, ("core:sample_count", 5L))]);
        SignalFiles.WriteSigmfCaptures(P("r"), [a, b]);
        Assert.Equal(ByHand.ReplaceLineEndings("\n"), File.ReadAllText(P("r.sigmf-meta")));
        Assert.Equal(SignalFiles.EncodeSamples([1.0, 2, 3, 4], "rf64_le"), File.ReadAllBytes(P("r.sigmf-data")));
    }

    [Fact]
    public void RoundTripsThroughTheReader()
    {
        const double rate = 3;
        Signal<Complex>[] parts =
        [
            Seg<Complex>([new(1, 1), 2], 0.25, -5, [At(1)], rate),
            Seg<Complex>([new(0, 3), 4, 5], 0.25 + 2 / rate, 7.5, null, rate),
            Seg<Complex>([], 0.25 + 5 / rate, 9, [At(4)], rate),
        ];
        SignalFiles.WriteSigmfCaptures(P("c"), parts, "cf32_le");
        var back = SignalFiles.ReadSigmfCaptures<Complex>(P("c"));
        Assert.Equal(3, back.Count);
        for (int j = 0; j < 3; j++)
        {
            Assert.Equal(parts[j].Samples.ToArray(), back[j].Samples.ToArray());
            Assert.Equal((parts[j].CenterFrequency, parts[j].TimeOrigin), (back[j].CenterFrequency, back[j].TimeOrigin));
            Assert.Equal(parts[j].Metadata.ContainsKey("core:annotations"), back[j].Metadata.ContainsKey("core:annotations"));
        }
        Assert.Equal(1L, ((Dictionary<string, object?>)((List<object?>)back[0].Metadata["core:annotations"]!)[0]!)["core:sample_start"]);
        Assert.Equal(4L, ((Dictionary<string, object?>)((List<object?>)back[2].Metadata["core:annotations"]!)[0]!)["core:sample_start"]);
        SignalFiles.WriteSigmfCaptures(P("d"), back, "cf32_le");
        SameFiles("c", "d");
    }

    [Fact]
    public void OneSegmentWritesTheWriteSigmfFiles()
    {
        var s = Seg([1.0, -2.0], 1.5, 3, [At(9)]);
        SignalFiles.WriteSigmf(P("a"), s);
        SignalFiles.WriteSigmfCaptures(P("b"), [s]);
        SameFiles("a", "b");
    }

    [Fact]
    public void ASingleEmptySegment()
    {
        SignalFiles.WriteSigmfCaptures(P("e"), [Seg<double>([], 0)]);
        Assert.Contains("\"core:sample_start\": 0", File.ReadAllText(P("e.sigmf-meta")), StringComparison.Ordinal);
        Assert.Equal(0, SignalFiles.ReadSigmfCaptures<double>(P("e"))[0].Length);
    }

    [Fact]
    public void TheTimeOriginMustBeExact()
    {
        // 0.1 + 2/10 is 0.30000000000000004 in binary64, so 0.3 is off by one ulp.
        var a = Seg([1.0, 2], 0.1, rate: 10);
        var e = Assert.ThrowsAny<ArgumentException>(() => SignalFiles.WriteSigmfCaptures(P("t"), [a, Seg([4.0], 0.3, rate: 10)]));
        Assert.Contains("time origin", e.Message, StringComparison.Ordinal);
        SignalFiles.WriteSigmfCaptures(P("t"), [a, Seg([4.0], 0.1 + 2 / 10.0, rate: 10)]);
    }

    [Fact]
    public void TheLastAnnotationMayRunPast()
    {
        SignalFiles.WriteSigmfCaptures(P("l"), [Seg([1.0], 0), Seg([2.0], 0.25, ann: [At(7)])]);
        var back = SignalFiles.ReadSigmfCaptures<double>(P("l"));
        Assert.Equal(7L, ((Dictionary<string, object?>)((List<object?>)back[1].Metadata["core:annotations"]!)[0]!)["core:sample_start"]);
    }

    public static TheoryData<int> Bad => [.. Enumerable.Range(0, 8)];

    private static Signal<double>[] BadCase(int i) => i switch
    {
        0 => [],
        1 => [Seg<double>([], 0), Seg([1.0], 0)],
        2 => [Seg([1.0], 0), Seg([2.0], 0.25, rate: 5)],
        3 => [Seg([1.0], 0), new Signal<double>([2.0], 4, 0, 0.25)],
        4 => [Seg([1.0], 0, ann: [At(1)]), Seg([2.0], 0.25)],
        5 => [Seg([1.0], 0), Seg([2.0], 0.25, ann: [At(1), At(0)])],
        6 => [Seg([1.0], 0), Seg([2.0], 0.25, double.NaN)],
        _ => [Seg([1.0], double.PositiveInfinity), Seg([2.0], double.PositiveInfinity)],
    };

    [Theory]
    [MemberData(nameof(Bad))]
    public void RejectsAndWritesNothing(int i)
    {
        Assert.ThrowsAny<ArgumentException>(() => SignalFiles.WriteSigmfCaptures(P("x"), BadCase(i)));
        Assert.Empty(Directory.GetFiles(_dir));
    }

    [Fact]
    public void RejectsNull()
    {
        Assert.Throws<ArgumentNullException>(() => SignalFiles.WriteSigmfCaptures<double>(P("x"), null!));
        Assert.Throws<ArgumentNullException>(() => SignalFiles.WriteSigmfCaptures(P("x"), [Seg([1.0], 0), null!]));
    }
}
