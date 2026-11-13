using System.Buffers.Binary;
using System.Collections;
using System.Globalization;
using System.Numerics;
using System.Runtime.InteropServices;
using System.Text.Encodings.Web;
using System.Text.Json;

namespace SignalForge;

/// <summary>
/// Signal files: raw sample encoding and SigMF-layout recordings, a <c>.sigmf-meta</c> JSON file
/// beside a <c>.sigmf-data</c> file of raw samples (conventions: Signal files). The sample kind is
/// the type argument: <c>double</c> for real, <see cref="Complex"/> for complex.
/// </summary>
public static class SignalFiles
{
    /// <summary>The SigMF version written into <c>core:version</c>.</summary>
    public const string SigmfVersion = "1.2.0";

    private static readonly HashSet<string> Reserved =
    [
        "core:datatype", "core:version", "core:sample_rate", "core:extensions",
        "core:num_channels", "core:dataset", "core:metadata_only",
    ];

    private readonly record struct Format(bool IsComplex, bool IsInteger, int Bits, bool BigEndian)
    {
        public int PartBytes => Bits / 8;
    }

    private static Format Parse(string? datatype, string paramName)
    {
        ArgumentNullException.ThrowIfNull(datatype, paramName);
        if (datatype.Length >= 3 && datatype[0] is 'c' or 'r')
        {
            string body = datatype[1..], order = "";
            int us = body.IndexOf('_', StringComparison.Ordinal);
            if (us >= 0)
                (body, order) = (body[..us], body[(us + 1)..]);
            int bits = body switch { "f64" => 64, "f32" or "i32" => 32, "i16" => 16, "i8" => 8, _ => 0 };
            bool orderOk = body == "i8" ? us < 0 : order is "le" or "be";
            if (bits > 0 && orderOk)
                return new Format(datatype[0] == 'c', body[0] == 'i', bits, order == "be");
        }
        throw new ArgumentException($"unknown datatype '{datatype}'", paramName);
    }

    /// <summary>The raw bytes of real samples as <paramref name="datatype"/>.</summary>
    /// <param name="x">Real samples.</param>
    /// <param name="datatype">A real datatype such as <c>rf32_le</c> or <c>ri16_be</c>.</param>
    public static byte[] EncodeSamples(ReadOnlySpan<double> x, string datatype)
    {
        var f = Parse(datatype, nameof(datatype));
        if (f.IsComplex)
            throw new ArgumentException($"{datatype} needs complex samples", nameof(x));
        return Encode(x, f, datatype);
    }

    /// <summary>The raw bytes of complex samples as <paramref name="datatype"/>, I then Q.</summary>
    /// <param name="x">Complex samples.</param>
    /// <param name="datatype">A complex datatype such as <c>cf32_le</c> or <c>ci16_be</c>.</param>
    public static byte[] EncodeSamples(ReadOnlySpan<Complex> x, string datatype)
    {
        var f = Parse(datatype, nameof(datatype));
        if (!f.IsComplex)
            throw new ArgumentException($"{datatype} needs real samples", nameof(x));
        return Encode(MemoryMarshal.Cast<Complex, double>(x), f, datatype);
    }

    private static byte[] Encode(ReadOnlySpan<double> parts, Format f, string datatype)
    {
        int w = f.PartBytes;
        var bytes = new byte[checked(parts.Length * w)];
        double scale = Math.ScaleB(1.0, f.Bits - 1);
        for (int i = 0; i < parts.Length; i++)
        {
            Span<byte> b = bytes.AsSpan(i * w, w);
            double v = parts[i];
            if (!f.IsInteger)
            {
                if (f.Bits == 64)
                    if (f.BigEndian) BinaryPrimitives.WriteDoubleBigEndian(b, v); else BinaryPrimitives.WriteDoubleLittleEndian(b, v);
                else if (f.BigEndian) BinaryPrimitives.WriteSingleBigEndian(b, (float)v);
                else BinaryPrimitives.WriteSingleLittleEndian(b, (float)v);
                continue;
            }
            if (!double.IsFinite(v))
                throw new ArgumentException($"{datatype} cannot hold non-finite samples", nameof(parts));
            double code = Math.Round(v * scale, MidpointRounding.ToEven);
            if (code < -scale || code > scale - 1)
                throw new ArgumentException($"a sample is outside the range of {datatype} (full scale is 1.0)", nameof(parts));
            switch (f.Bits)
            {
                case 32 when f.BigEndian: BinaryPrimitives.WriteInt32BigEndian(b, (int)code); break;
                case 32: BinaryPrimitives.WriteInt32LittleEndian(b, (int)code); break;
                case 16 when f.BigEndian: BinaryPrimitives.WriteInt16BigEndian(b, (short)code); break;
                case 16: BinaryPrimitives.WriteInt16LittleEndian(b, (short)code); break;
                default: b[0] = unchecked((byte)(sbyte)code); break;
            }
        }
        return bytes;
    }

    /// <summary>Samples from the raw bytes of <paramref name="datatype"/>, in double precision.</summary>
    /// <typeparam name="T"><c>double</c> for a real datatype, <see cref="Complex"/> for a complex one.</typeparam>
    /// <param name="data">The bytes: a whole number of samples.</param>
    /// <param name="datatype">The datatype, such as <c>ci16_le</c>.</param>
    public static T[] DecodeSamples<T>(ReadOnlySpan<byte> data, string datatype) where T : struct
    {
        var f = Parse(datatype, nameof(datatype));
        CheckKind<T>(f, datatype, nameof(datatype));
        int w = f.PartBytes, size = w * (f.IsComplex ? 2 : 1);
        if (data.Length % size != 0)
            throw new ArgumentException($"{data.Length} bytes is not a whole number of {datatype} samples", nameof(data));
        var parts = new double[data.Length / w];
        double scale = Math.ScaleB(1.0, f.Bits - 1);
        for (int i = 0; i < parts.Length; i++)
        {
            ReadOnlySpan<byte> b = data.Slice(i * w, w);
            parts[i] = (f.IsInteger, f.Bits, f.BigEndian) switch
            {
                (false, 64, true) => BinaryPrimitives.ReadDoubleBigEndian(b),
                (false, 64, false) => BinaryPrimitives.ReadDoubleLittleEndian(b),
                (false, _, true) => BinaryPrimitives.ReadSingleBigEndian(b),
                (false, _, false) => BinaryPrimitives.ReadSingleLittleEndian(b),
                (true, 32, true) => BinaryPrimitives.ReadInt32BigEndian(b) / scale,
                (true, 32, false) => BinaryPrimitives.ReadInt32LittleEndian(b) / scale,
                (true, 16, true) => BinaryPrimitives.ReadInt16BigEndian(b) / scale,
                (true, 16, false) => BinaryPrimitives.ReadInt16LittleEndian(b) / scale,
                _ => (sbyte)b[0] / scale,
            };
        }
        if (!f.IsComplex)
            return (T[])(object)parts;
        var z = new Complex[parts.Length / 2];
        for (int i = 0; i < z.Length; i++)
            z[i] = new Complex(parts[2 * i], parts[2 * i + 1]);
        return (T[])(object)z;
    }

    private static void CheckKind<T>(Format f, string datatype, string paramName)
    {
        bool wantComplex = typeof(T) == typeof(Complex);
        if (!wantComplex && typeof(T) != typeof(double))
            throw new ArgumentException($"the sample type must be double or Complex, not {typeof(T).Name}", paramName);
        if (f.IsComplex != wantComplex)
            throw new ArgumentException($"{datatype} holds {(f.IsComplex ? "complex" : "real")} samples, not {typeof(T).Name}", paramName);
    }

    private static (string Meta, string Data) Files(string path)
    {
        ArgumentException.ThrowIfNullOrEmpty(path);
        string b = path.EndsWith(".sigmf-meta", StringComparison.Ordinal) || path.EndsWith(".sigmf-data", StringComparison.Ordinal)
            ? path[..^".sigmf-meta".Length]
            : path;
        return (b + ".sigmf-meta", b + ".sigmf-data");
    }

    /// <summary>Writes <paramref name="signal"/> as <c>&lt;base&gt;.sigmf-data</c> and <c>&lt;base&gt;.sigmf-meta</c>.</summary>
    /// <typeparam name="T"><c>double</c> or <see cref="Complex"/>.</typeparam>
    /// <param name="path">The base path, or either file's name.</param>
    /// <param name="signal">The signal; its metadata must be JSON data.</param>
    /// <param name="datatype">The sample datatype; null for <c>cf64_le</c> or <c>rf64_le</c>, which lose nothing.</param>
    public static void WriteSigmf<T>(string path, Signal<T> signal, string? datatype = null) where T : struct
    {
        ArgumentNullException.ThrowIfNull(signal);
        bool isComplex = typeof(T) == typeof(Complex);
        datatype ??= isComplex ? "cf64_le" : "rf64_le";
        var f = Parse(datatype, nameof(datatype));
        CheckKind<T>(f, datatype, nameof(datatype));
        byte[] data = isComplex
            ? EncodeSamples(MemoryMarshal.Cast<T, Complex>(signal.Samples), datatype)
            : EncodeSamples(MemoryMarshal.Cast<T, double>(signal.Samples), datatype);
        Check.Finite(signal.TimeOrigin, nameof(signal));
        Check.Finite(signal.CenterFrequency, nameof(signal));

        var buffer = new MemoryStream();
        var options = new JsonWriterOptions { Indented = true, NewLine = "\n", Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping };
        using (var w = new Utf8JsonWriter(buffer, options))
        {
            w.WriteStartObject();
            w.WriteStartObject("global");
            w.WriteString("core:datatype", datatype);
            w.WriteString("core:version", SigmfVersion);
            w.WritePropertyName("core:sample_rate");
            WriteDouble(w, signal.SampleRate);
            w.WriteStartArray("core:extensions");
            w.WriteStartObject();
            w.WriteString("name", "signalforge");
            w.WriteString("version", "1.0.0");
            w.WriteBoolean("optional", true);
            w.WriteEndObject();
            w.WriteEndArray();
            w.WritePropertyName("signalforge:time_origin");
            WriteDouble(w, signal.TimeOrigin);
            if (signal.Units is { } units)
                w.WriteString("signalforge:units", units);
            if (signal.Impedance is { } r)
            {
                w.WritePropertyName("signalforge:impedance");
                WriteDouble(w, r);
            }
            var plain = signal.Metadata.Where(kv => !kv.Key.Contains(':', StringComparison.Ordinal)).ToList();
            if (plain.Count > 0)
            {
                w.WriteStartObject("signalforge:metadata");
                foreach (var (k, v) in plain)
                {
                    w.WritePropertyName(k);
                    WriteValue(w, v, k);
                }
                w.WriteEndObject();
            }
            foreach (var (k, v) in signal.Metadata.Where(kv => kv.Key.Contains(':', StringComparison.Ordinal)))
            {
                if (Reserved.Contains(k) || k.StartsWith("signalforge:", StringComparison.Ordinal))
                    throw new ArgumentException($"metadata key '{k}' is reserved", nameof(signal));
                w.WritePropertyName(k);
                WriteValue(w, v, k);
            }
            w.WriteEndObject();
            w.WriteStartArray("captures");
            w.WriteStartObject();
            w.WriteNumber("core:sample_start", 0);
            w.WritePropertyName("core:frequency");
            WriteDouble(w, signal.CenterFrequency);
            w.WriteEndObject();
            w.WriteEndArray();
            w.WriteStartArray("annotations");
            w.WriteEndArray();
            w.WriteEndObject();
        }
        buffer.WriteByte((byte)'\n');
        var (meta, dataPath) = Files(path);
        File.WriteAllBytes(dataPath, data);
        File.WriteAllBytes(meta, buffer.ToArray());
    }

    /// <summary>A float with a fraction or an exponent, so a reader sees a float, not an integer.</summary>
    private static void WriteDouble(Utf8JsonWriter w, double d)
    {
        string s = d.ToString("R", CultureInfo.InvariantCulture);
        w.WriteRawValue(s.Contains('.', StringComparison.Ordinal) || s.Contains('E', StringComparison.Ordinal) ? s : s + ".0");
    }

    private static void WriteValue(Utf8JsonWriter w, object? v, string where)
    {
        switch (v)
        {
            case null: w.WriteNullValue(); break;
            case string s: w.WriteStringValue(s); break;
            case bool b: w.WriteBooleanValue(b); break;
            case sbyte or byte or short or ushort or int or uint or long:
                w.WriteNumberValue(Convert.ToInt64(v, CultureInfo.InvariantCulture)); break;
            case ulong u: w.WriteNumberValue(u); break;
            case float or double:
                double d = Convert.ToDouble(v, CultureInfo.InvariantCulture);
                if (!double.IsFinite(d))
                    throw new ArgumentException($"metadata {where}: JSON cannot hold {d}");
                WriteDouble(w, d);
                break;
            case IDictionary map:
                w.WriteStartObject();
                foreach (DictionaryEntry e in map)
                {
                    if (e.Key is not string k)
                        throw new ArgumentException($"metadata {where}: object keys must be strings");
                    w.WritePropertyName(k);
                    WriteValue(w, e.Value, $"{where}.{k}");
                }
                w.WriteEndObject();
                break;
            case IEnumerable items:
                w.WriteStartArray();
                int i = 0;
                foreach (object? x in items)
                    WriteValue(w, x, $"{where}[{i++}]");
                w.WriteEndArray();
                break;
            default:
                throw new ArgumentException($"metadata {where}: {v.GetType().Name} is not JSON data");
        }
    }

    /// <summary>Reads a <c>.sigmf-meta</c> / <c>.sigmf-data</c> pair as a signal.</summary>
    /// <typeparam name="T"><c>double</c> for a real recording, <see cref="Complex"/> for a complex one.</typeparam>
    /// <param name="path">The base path, or either file's name.</param>
    /// <exception cref="ArgumentException">The recording is malformed or of the other kind.</exception>
    /// <exception cref="IOException">A file is missing or unreadable.</exception>
    public static Signal<T> ReadSigmf<T>(string path) where T : struct
    {
        var (metaPath, dataPath) = Files(path);
        byte[] text = File.ReadAllBytes(metaPath);
        object? doc;
        try
        {
            using var json = JsonDocument.Parse(text);
            doc = ToValue(json.RootElement);
        }
        catch (JsonException e)
        {
            throw new ArgumentException($"{metaPath}: not valid JSON: {e.Message}", nameof(path), e);
        }
        var top = Obj(doc, "the metadata");
        var glob = Obj(top.GetValueOrDefault("global"), "global");
        if (glob.GetValueOrDefault("core:datatype") is not string datatype)
            throw new ArgumentException("core:datatype is required", nameof(path));
        if (glob.GetValueOrDefault("core:version") is not string version || !version.StartsWith("1.", StringComparison.Ordinal))
            throw new ArgumentException("unsupported core:version", nameof(path));
        double rate = Num(glob.GetValueOrDefault("core:sample_rate"), "core:sample_rate");
        if (glob.TryGetValue("core:num_channels", out var nc) && nc is not 1L)
            throw new ArgumentException("only single-channel recordings are supported", nameof(path));
        foreach (string k in (string[])["core:dataset", "core:metadata_only"])
            if (glob.ContainsKey(k))
                throw new ArgumentException($"{k} recordings are not supported", nameof(path));
        var captures = top.GetValueOrDefault("captures") ?? new List<object?>();
        if (captures is not List<object?> caps)
            throw new ArgumentException("captures must be a JSON array", nameof(path));
        var freqs = new HashSet<double>();
        for (int i = 0; i < caps.Count; i++)
        {
            var c = Obj(caps[i], $"captures[{i}]");
            if (c.TryGetValue("core:header_bytes", out var hb) && hb is not 0L)
                throw new ArgumentException("captures with header bytes are not supported", nameof(path));
            freqs.Add(c.TryGetValue("core:frequency", out var fq) ? Num(fq, $"captures[{i}] core:frequency") : 0.0);
        }
        if (freqs.Count > 1)
            throw new ArgumentException("captures at different frequencies are not supported", nameof(path));
        object? units = glob.GetValueOrDefault("signalforge:units");
        if (units is not (null or string))
            throw new ArgumentException("signalforge:units must be a string", nameof(path));
        object? impedance = glob.GetValueOrDefault("signalforge:impedance");
        var metadata = new Dictionary<string, object?>(
            Obj(glob.GetValueOrDefault("signalforge:metadata") ?? new Dictionary<string, object?>(), "signalforge:metadata"));
        foreach (var (k, v) in glob)
            if (!Reserved.Contains(k) && !k.StartsWith("signalforge:", StringComparison.Ordinal))
                metadata[k] = v;
        double timeOrigin = glob.TryGetValue("signalforge:time_origin", out var t0) ? Num(t0, "signalforge:time_origin") : 0.0;
        T[] samples = DecodeSamples<T>(File.ReadAllBytes(dataPath), datatype);
        return new Signal<T>(samples, rate, freqs.Count == 1 ? freqs.First() : 0.0, timeOrigin, (string?)units,
            impedance is null ? null : Num(impedance, "signalforge:impedance"), metadata);
    }

    private static Dictionary<string, object?> Obj(object? v, string what) =>
        v as Dictionary<string, object?> ?? throw new ArgumentException($"{what} must be a JSON object");

    private static double Num(object? v, string what) => v switch
    {
        long l => l,
        double d when double.IsFinite(d) => d,
        _ => throw new ArgumentException($"{what} must be a finite number"),
    };

    /// <summary>JSON to plain values: string, bool, null, long (no fraction or exponent), double,
    /// List, Dictionary. Duplicate keys are an error.</summary>
    private static object? ToValue(JsonElement e)
    {
        switch (e.ValueKind)
        {
            case JsonValueKind.Object:
                var map = new Dictionary<string, object?>();
                foreach (var p in e.EnumerateObject())
                    if (!map.TryAdd(p.Name, ToValue(p.Value)))
                        throw new JsonException($"duplicate JSON key '{p.Name}'");
                return map;
            case JsonValueKind.Array:
                return e.EnumerateArray().Select(ToValue).ToList();
            case JsonValueKind.String:
                return e.GetString();
            case JsonValueKind.True:
                return true;
            case JsonValueKind.False:
                return false;
            case JsonValueKind.Number:
                string raw = e.GetRawText();
                return raw.AsSpan().IndexOfAny(".eE") < 0 && e.TryGetInt64(out long l) ? (object)l : e.GetDouble();
            default:
                return null;
        }
    }
}
