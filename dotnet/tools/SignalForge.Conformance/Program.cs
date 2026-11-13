using System.Text.Json;
using System.Text.Json.Serialization;
using SignalForge;
using SignalForge.Tests;

// Usage (exit 0 when everything passes, 1 when a vector fails, 2 for bad input):
//   SignalForge.Conformance [VECTORS_DIR] [--report PATH]   run the vectors
//   SignalForge.Conformance link CONFIG.json [--out PATH]    run one QPSK link; print or write its JSON report
const string Usage = "usage: SignalForge.Conformance [VECTORS_DIR] [--report PATH] | link CONFIG.json [--out PATH]";

try
{
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
