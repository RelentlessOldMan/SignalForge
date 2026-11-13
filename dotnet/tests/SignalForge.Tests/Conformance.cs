using System.Globalization;
using System.Numerics;
using System.Reflection;
using System.Text;
using System.Text.Json;

namespace SignalForge.Tests;

/// <summary>Loads and runs the shared vectors in vectors/cases. Format: vectors/README.md.</summary>
public static class Conformance
{
    private const double DefaultAbs = 1e-12, DefaultRel = 1e-12;

    public sealed record VectorCase(string File, string Id, JsonElement Json)
    {
        public override string ToString() => $"{File}:{Id}";
    }

    public static string VectorsDir()
    {
        for (var d = new DirectoryInfo(AppContext.BaseDirectory); d is not null; d = d.Parent)
        {
            string cand = Path.Combine(d.FullName, "vectors", "cases");
            if (Directory.Exists(cand))
                return cand;
        }
        throw new DirectoryNotFoundException("vectors/cases not found above " + AppContext.BaseDirectory);
    }

    public static IEnumerable<VectorCase> LoadCases(string? dir = null)
    {
        foreach (string path in Directory.GetFiles(dir ?? VectorsDir(), "*.json").Order(StringComparer.Ordinal))
        {
            using var doc = JsonDocument.Parse(File.ReadAllText(path));
            var root = doc.RootElement;
            if (root.GetProperty("schema").GetInt32() != 1)
                throw new InvalidDataException($"{Path.GetFileName(path)}: unsupported schema");
            foreach (var c in root.GetProperty("cases").EnumerateArray())
                yield return new VectorCase(Path.GetFileName(path), c.GetProperty("id").GetString()!, c.Clone());
        }
    }

    /// <summary>Runs one case; returns the failure messages (empty when it passes).</summary>
    public static List<string> Run(VectorCase c)
    {
        var json = c.Json;
        string op = json.GetProperty("op").GetString()!;
        var args = new Dictionary<string, object?>();
        if (json.TryGetProperty("args", out var a))
            foreach (var p in a.EnumerateObject())
                args[p.Name] = Decode(p.Value);
        double abs = DefaultAbs, rel = DefaultRel;
        if (json.TryGetProperty("tol", out var tol))
        {
            if (tol.TryGetProperty("abs", out var t)) abs = t.GetDouble();
            if (tol.TryGetProperty("rel", out t)) rel = t.GetDouble();
        }
        bool wantError = json.TryGetProperty("error", out var err);

        object? actual;
        try
        {
            actual = Invoke(op, args);
        }
        catch (ArgumentException e)
        {
            return wantError && err.GetString() == "invalid_argument" ? [] : [$"threw {e.GetType().Name}: {e.Message}"];
        }
        if (wantError)
            return [$"expected error {err.GetString()}"];
        var msgs = new List<string>();
        Compare(Canonical(actual), Decode(json.GetProperty("expected")), abs, rel, "", msgs);
        return msgs;
    }

    private static object? Invoke(string op, Dictionary<string, object?> a)
    {
        double D(string k) => Convert.ToDouble(a[k], CultureInfo.InvariantCulture);
        double Opt(string k, double dflt) => a.ContainsKey(k) ? D(k) : dflt;
        int I(string k) => checked((int)D(k));
        int? OptInt(string k) => a.ContainsKey(k) ? I(k) : null;
        bool Flag(string k) => a.TryGetValue(k, out var f) && f is true;
        return op switch
        {
            "lin_to_db" => Units.LinToDb(D("x")),
            "db_to_lin" => Units.DbToLin(D("x")),
            "amp_to_db" => Units.AmpToDb(D("x")),
            "db_to_amp" => Units.DbToAmp(D("x")),
            "w_to_dbm" => Units.WToDbm(D("x")),
            "dbm_to_w" => Units.DbmToW(D("x")),
            "vrms_to_dbm" => Units.VrmsToDbm(D("vrms"), Opt("impedance", Units.DefaultImpedance)),
            "dbm_to_vrms" => Units.DbmToVrms(D("dbm"), Opt("impedance", Units.DefaultImpedance)),
            "tone" => a.TryGetValue("complex", out var cx) && cx is false
                ? Waveforms.RealTone(D("sample_rate"), I("num_samples"), D("frequency"), Opt("amplitude", 1), Opt("phase", 0))
                : Waveforms.Tone(D("sample_rate"), I("num_samples"), D("frequency"), Opt("amplitude", 1), Opt("phase", 0)),
            "prbs" => Waveforms.Prbs(I("order"), I("num_bits"),
                a.ContainsKey("seed") ? checked((uint)D("seed")) : null, a.TryGetValue("invert", out var inv) && inv is true),
            "power_stats" => a["samples"] is Complex[] cs ? Measurements.PowerStats(cs) : Measurements.PowerStats(Reals(a["samples"])),
            "qpsk_map" => Modulation.QpskMap(Bits(a["bits"])),
            "qpsk_demap_hard" => Modulation.QpskDemapHard(Complexes(a["symbols"])),
            "bit_errors" => Metrics.BitErrors(Bits(a["reference"]), Bits(a["received"])),
            "fft" => a["samples"] is Complex[] fc ? Spectral.Fft(fc) : Spectral.Fft(Reals(a["samples"])),
            "ifft" => Spectral.Ifft(Complexes(a["spectrum"])),
            "fft_frequencies" => Spectral.FftFrequencies(I("n"), D("sample_rate"), Flag("shifted")),
            "window" => Spectral.Window(WindowName(a["name"]), I("n"), Flag("symmetric"),
                a.ContainsKey("beta") ? D("beta") : null),
            "window_stats" => Spectral.WindowStats(Reals(a["w"])),
            "welch_psd" => a["samples"] is Complex[] ws
                ? Spectral.WelchPsd(ws, D("sample_rate"), OptInt("nperseg"), OptInt("noverlap"), WindowName(a.GetValueOrDefault("window", "hann")))
                : Spectral.WelchPsd(Reals(a["samples"]), D("sample_rate"), OptInt("nperseg"), OptInt("noverlap"),
                    WindowName(a.GetValueOrDefault("window", "hann")), !a.TryGetValue("one_sided", out var os) || os is true),
            "occupied_bandwidth" => Spectral.OccupiedBandwidth(Reals(a["frequencies"]), Reals(a["psd"]), Opt("fraction", 0.99)),
            "channel_power" => Spectral.ChannelPower(Reals(a["frequencies"]), Reals(a["psd"]), D("low"), D("high")),
            _ => throw new InvalidOperationException($"unknown op {op}"),
        };
    }

    /// <summary>Vector window name (snake_case) to the enum; unknown names throw ArgumentException.</summary>
    private static WindowType WindowName(object? v) =>
        Enum.Parse<WindowType>(((string)v!).Replace("_", "", StringComparison.Ordinal), ignoreCase: true);

    private static double[] Reals(object? v) => v as double[] ?? throw new InvalidDataException("expected a real array");

    private static Complex[] Complexes(object? v) =>
        v as Complex[] ?? Reals(v).Select(x => new Complex(x, 0)).ToArray();

    private static byte[] Bits(object? v) => Reals(v).Select(x =>
        x is >= 0 and <= byte.MaxValue && x == Math.Floor(x)
            ? (byte)x
            : throw new ArgumentException($"not a bit value: {x}")).ToArray();

    /// <summary>JSON vector value to: double, bool, string, double[], Complex, Complex[], or a record dictionary.</summary>
    public static object? Decode(JsonElement v)
    {
        switch (v.ValueKind)
        {
            case JsonValueKind.Number:
                return v.GetDouble();
            case JsonValueKind.True:
                return true;
            case JsonValueKind.False:
                return false;
            case JsonValueKind.String:
                return v.GetString() switch
                {
                    "inf" => double.PositiveInfinity,
                    "-inf" => double.NegativeInfinity,
                    "nan" => double.NaN,
                    var s => s,
                };
            case JsonValueKind.Array:
                return v.EnumerateArray().Select(e => (double)Decode(e)!).ToArray();
            case JsonValueKind.Object:
                var props = v.EnumerateObject().ToList();
                if (props.Count == 2 && v.TryGetProperty("re", out var re) && v.TryGetProperty("im", out var im))
                {
                    if (re.ValueKind == JsonValueKind.Array)
                    {
                        var r = (double[])Decode(re)!;
                        var i = (double[])Decode(im)!;
                        return r.Zip(i, (x, y) => new Complex(x, y)).ToArray();
                    }
                    return new Complex((double)Decode(re)!, (double)Decode(im)!);
                }
                return props.ToDictionary(p => p.Name, p => Decode(p.Value));
            default:
                return null;
        }
    }

    /// <summary>Result to the decoded-vector shape: numbers as double, arrays as double[]/Complex[], records as snake_case dictionaries.</summary>
    public static object? Canonical(object? v) => v switch
    {
        null => null,
        double or Complex or Complex[] or double[] or bool or string => v,
        int i => (double)i,
        byte[] b => b.Select(x => (double)x).ToArray(),
        _ when v.GetType().Assembly == typeof(Units).Assembly =>
            v.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance)
                .ToDictionary(p => SnakeCase(p.Name), p => Canonical(p.GetValue(v))),
        _ => throw new InvalidOperationException($"no canonical form for {v.GetType()}"),
    };

    public static string SnakeCase(string name)
    {
        var sb = new StringBuilder();
        for (int i = 0; i < name.Length; i++)
        {
            if (char.IsUpper(name[i]) && i > 0)
                sb.Append('_');
            sb.Append(char.ToLowerInvariant(name[i]));
        }
        return sb.ToString();
    }

    private static void Compare(object? actual, object? expected, double abs, double rel, string path, List<string> msgs)
    {
        string where = path.Length == 0 ? "value" : path;
        switch (expected)
        {
            case Dictionary<string, object?> rec:
                if (actual is not Dictionary<string, object?> act)
                {
                    msgs.Add($"{where}: expected a record, got {actual?.GetType().Name ?? "null"}");
                    return;
                }
                foreach (var (k, e) in rec)
                {
                    string p = path.Length == 0 ? k : $"{path}.{k}";
                    if (act.TryGetValue(k, out var x)) Compare(x, e, abs, rel, p, msgs);
                    else msgs.Add($"{p}: missing");
                }
                return;
            case double[] ed when actual is double[] ad:
                CompareArrays(ad.Select(x => new Complex(x, 0)).ToArray(), ed.Select(x => new Complex(x, 0)).ToArray(), abs, rel, where, msgs);
                return;
            case Complex[] ec when actual is Complex[] ac:
                CompareArrays(ac, ec, abs, rel, where, msgs);
                return;
            case bool eb when actual is bool ab:
                if (ab != eb) msgs.Add($"{where}: {ab} != expected {eb}");
                return;
            case double ed when actual is double ad:
                if (!Close(ad, ed, abs, rel)) msgs.Add($"{where}: {ad:R} != expected {ed:R}");
                return;
            case Complex ec when actual is Complex ac:
                if (!Close(ac, ec, abs, rel)) msgs.Add($"{where}: {ac} != expected {ec}");
                return;
            default:
                msgs.Add($"{where}: type {actual?.GetType().Name ?? "null"} does not match expected {expected?.GetType().Name ?? "null"}");
                return;
        }
    }

    private static void CompareArrays(Complex[] a, Complex[] e, double abs, double rel, string where, List<string> msgs)
    {
        if (a.Length != e.Length)
        {
            msgs.Add($"{where}: length {a.Length} != expected {e.Length}");
            return;
        }
        var bad = Enumerable.Range(0, e.Length).Where(i => !Close(a[i], e[i], abs, rel)).ToList();
        if (bad.Count > 0)
            msgs.Add($"{where}[{bad[0]}]: {a[bad[0]]} != expected {e[bad[0]]} ({bad.Count} differ)");
    }

    private static bool Close(double a, double e, double abs, double rel)
    {
        if (double.IsNaN(e)) return double.IsNaN(a);
        if (double.IsInfinity(e)) return a == e;
        return Math.Abs(a - e) <= abs + rel * Math.Abs(e);
    }

    private static bool Close(Complex a, Complex e, double abs, double rel) =>
        Complex.Abs(a - e) <= abs + rel * Complex.Abs(e);
}
