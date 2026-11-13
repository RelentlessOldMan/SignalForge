using System.Text.Json;
using SignalForge;
using SignalForge.Tests;

// Usage:
//   SignalForge.Conformance [VECTORS_DIR] [--report PATH]   run the vectors; exit 1 if any fail
//   SignalForge.Conformance link CONFIG.json [--out PATH]    run one QPSK link; print or write its JSON report
if (args is ["link", var configPath, ..] && (args.Length == 2 || args is [_, _, "--out", _]))
{
    var options = new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower, UnmappedMemberHandling = System.Text.Json.Serialization.JsonUnmappedMemberHandling.Disallow };
    var config = JsonSerializer.Deserialize<QpskLinkConfig>(File.ReadAllText(configPath), options)
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
        Console.Error.WriteLine("usage: SignalForge.Conformance [VECTORS_DIR] [--report PATH] | link CONFIG.json [--out PATH]");
        return 2;
    }
}
string tmp = report ?? Path.Combine(Path.GetTempPath(), $"signalforge-conformance-{Environment.ProcessId}.json");
int failed = Conformance.WriteReport(tmp, dir, Console.Out);
if (report is null)
    File.Delete(tmp);
return failed > 0 ? 1 : 0;
