using System.Numerics;
using System.Text.Json;
using System.Text.Json.Serialization;
using SignalForge;
using SignalForge.Tests;

// Usage (exit 0 when everything passes, 1 when a vector fails, 2 for bad input):
//   SignalForge.Conformance [VECTORS_DIR] [--report PATH]   run the vectors
//   SignalForge.Conformance link CONFIG.json [--out PATH]    run one QPSK link; print or write its JSON report
//   SignalForge.Conformance write-files DIR                  write the exchange recordings (one per datatype)
//   SignalForge.Conformance read-files DIR [--out PATH]      read every recording in DIR into a JSON report
const string Usage = "usage: SignalForge.Conformance [VECTORS_DIR] [--report PATH] | link CONFIG.json [--out PATH]"
    + " | write-files DIR | read-files DIR [--out PATH]";

try
{
    if (args is ["write-files", string writeDir])
    {
        Exchange.Write(writeDir);
        return 0;
    }
    if (args is ["read-files", ..])
    {
        if (args is not ([_, _] or [_, _, "--out", _]))
        {
            Console.Error.WriteLine(Usage);
            return 2;
        }
        string json = JsonSerializer.Serialize(Exchange.Read(args[1]), new JsonSerializerOptions { WriteIndented = true });
        if (args.Length == 4)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(args[3]))!);
            File.WriteAllText(args[3], json + "\n");
        }
        else
            Console.WriteLine(json);
        return 0;
    }
    if (args is ["link", ..])
    {
        if (args is not ([_, _] or [_, _, "--out", _]))
        {
            Console.Error.WriteLine(Usage);
            return 2;
        }
        var options = new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
            UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow,
        };
        var config = JsonSerializer.Deserialize<QpskLinkConfig>(File.ReadAllText(args[1]), options)
            ?? throw new InvalidDataException("the config is null");
        string json = Link.QpskLink(config).ToJson();
        if (args.Length == 4)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(args[3]))!);
            File.WriteAllText(args[3], json + "\n");
        }
        else
            Console.WriteLine(json);
        return 0;
    }

    string? dir = null, report = null;
    for (int i = 0; i < args.Length; i++)
    {
        if (args[i] == "--report" && i + 1 < args.Length)
            report = args[++i];
        else if (dir is null && !args[i].StartsWith('-'))
            dir = args[i];
        else
        {
            Console.Error.WriteLine(Usage);
            return 2;
        }
    }
    return Conformance.WriteReport(report, dir, Console.Out) > 0 ? 1 : 0;
}
catch (Exception e) when (e is IOException or UnauthorizedAccessException or JsonException or ArgumentException or InvalidDataException)
{
    Console.Error.WriteLine($"error: {e.GetType().Name}: {e.Message}");
    return 2;
}

/// <summary>The file exchange check: the recordings this side writes, and the report of what it reads
/// (the Python side is <c>python -m signalforge.compare write-files / read-files / files</c>).</summary>
internal static class Exchange
{
    private static IEnumerable<string> Datatypes() =>
        from k in "cr"
        from t in (string[])["f64_le", "f64_be", "f32_le", "f32_be", "i32_le", "i32_be", "i16_le", "i16_be", "i8", "u32_le", "u32_be", "u16_le", "u16_be", "u8"]
        select $"{k}{t}";

    public static void Write(string dir)
    {
        Directory.CreateDirectory(dir);
        var z = new Complex[64];
        for (int k = 0; k < z.Length; k++)
        {
            double a = 0.45 * (1 + Math.Cos(2 * Math.PI * k / 64)), th = 2 * Math.PI * 0.05 * k;
            z[k] = new Complex(a * Math.Cos(th), a * Math.Sin(th));
        }
        var meta = new Dictionary<string, object?>
        {
            ["writer"] = "dotnet",
            ["run"] = 7,
            ["gains"] = new object[] { 1, 2.5 },
            ["core:author"] = "signalforge",
        };
        foreach (string dt in Datatypes())
        {
            string path = Path.Combine(dir, $"dotnet-{dt}");
            if (dt[0] == 'c')
                SignalFiles.WriteSigmf(path, new Signal<Complex>(z, 48000, 915e6, -0.25, "V", 50, meta), dt);
            else
                SignalFiles.WriteSigmf(path, new Signal<double>([.. z.Select(c => c.Real)], 48000, 0, -0.25, "V", 50, meta), dt);
        }
    }

    public static Dictionary<string, object?> Read(string dir)
    {
        var files = new SortedDictionary<string, object?>(StringComparer.Ordinal);
        foreach (string meta in Directory.GetFiles(dir, "*.sigmf-meta"))
        {
            using var doc = JsonDocument.Parse(File.ReadAllBytes(meta));
            bool isComplex = doc.RootElement.GetProperty("global").GetProperty("core:datatype").GetString()?.StartsWith('c') == true;
            files[Path.GetFileName(meta)[..^".sigmf-meta".Length]] = isComplex
                ? Record(SignalFiles.ReadSigmf<Complex>(meta), x => x.Select(c => c.Real), x => x.Select(c => c.Imaginary))
                : Record(SignalFiles.ReadSigmf<double>(meta), x => x, null);
        }
        return new() { ["files"] = files };
    }

    private static Dictionary<string, object?> Record<T>(Signal<T> s, Func<T[], IEnumerable<double>> re, Func<T[], IEnumerable<double>>? im)
        where T : struct
    {
        T[] x = s.Samples.ToArray();
        return new()
        {
            ["re"] = re(x).ToArray(),
            ["im"] = im?.Invoke(x).ToArray(),
            ["sample_rate"] = s.SampleRate,
            ["center_frequency"] = s.CenterFrequency,
            ["time_origin"] = s.TimeOrigin,
            ["units"] = s.Units,
            ["impedance"] = s.Impedance,
            ["metadata"] = s.Metadata,
        };
    }
}
