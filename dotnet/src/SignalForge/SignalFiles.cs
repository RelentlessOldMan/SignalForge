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

    /// <summary>Deepest nesting of objects and arrays in a <c>.sigmf-meta</c> file; the top object is level 1.</summary>
    public const int MaxDepth = 64;

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
                w.WriteString("signalforge:units", Text(units, "units"));
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
                    w.WritePropertyName(Text(k, k));
                    WriteValue(w, v, k, 4);
                }
                w.WriteEndObject();
            }
            foreach (var (k, v) in signal.Metadata.Where(kv => kv.Key.Contains(':', StringComparison.Ordinal)))
            {
                if (Reserved.Contains(k) || k.StartsWith("signalforge:", StringComparison.Ordinal))
                    throw new ArgumentException($"metadata key '{k}' is reserved", nameof(signal));
                w.WritePropertyName(Text(k, k));
                WriteValue(w, v, k, 3);
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

    /// <summary>Writes metadata value <paramref name="v"/>; an object or array would sit at
    /// <paramref name="depth"/> (the document's top object is level 1).</summary>
    private static void WriteValue(Utf8JsonWriter w, object? v, string where, int depth)
    {
        if (v is IEnumerable and not string && depth > MaxDepth)
            throw new ArgumentException($"metadata {where}: nested deeper than {MaxDepth} levels");
        switch (v)
        {
            case null: w.WriteNullValue(); break;
            case string s: w.WriteStringValue(Text(s, $"metadata {where}")); break;
            case bool b: w.WriteBooleanValue(b); break;
            case sbyte or byte or short or ushort or int or uint or long:
                w.WriteNumberValue(Convert.ToInt64(v, CultureInfo.InvariantCulture)); break;
            case ulong u when u <= long.MaxValue: w.WriteNumberValue(u); break;
            case ulong:
                throw new ArgumentException($"metadata {where}: integer outside the signed 64-bit range");
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
                    w.WritePropertyName(Text(k, $"metadata {where}"));
                    WriteValue(w, e.Value, $"{where}.{k}", depth + 1);
                }
                w.WriteEndObject();
                break;
            case IEnumerable items:
                w.WriteStartArray();
                int i = 0;
                foreach (object? x in items)
                    WriteValue(w, x, $"{where}[{i++}]", depth + 1);
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
            using var json = JsonDocument.Parse(text, new JsonDocumentOptions { MaxDepth = MaxDepth });
            doc = ToValue(json.RootElement);
        }
        catch (Exception e) when (e is JsonException or InvalidOperationException)
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
        object? captures = top.TryGetValue("captures", out var cv) ? cv : new List<object?>();
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
            Obj(glob.TryGetValue("signalforge:metadata", out var mv) ? mv : new Dictionary<string, object?>(), "signalforge:metadata"));
        foreach (var (k, v) in glob)
            if (!Reserved.Contains(k) && !k.StartsWith("signalforge:", StringComparison.Ordinal))
                metadata[k] = v;
        double timeOrigin = glob.TryGetValue("signalforge:time_origin", out var t0) ? Num(t0, "signalforge:time_origin") : 0.0;
        T[] samples = DecodeSamples<T>(File.ReadAllBytes(dataPath), datatype);
        return new Signal<T>(samples, rate, freqs.Count == 1 ? freqs.First() : 0.0, timeOrigin, (string?)units,
            impedance is null ? null : Num(impedance, "signalforge:impedance"), metadata);
    }

    /// <summary><paramref name="s"/>, or an exception if it has a lone surrogate (not valid Unicode).</summary>
    private static string Text(string s, string where, bool read = false)
    {
        for (int i = 0; i < s.Length; i++)
        {
            if (char.IsHighSurrogate(s[i]) && i + 1 < s.Length && char.IsLowSurrogate(s[i + 1]))
                i++;
            else if (char.IsSurrogate(s[i]))
                throw read
                    ? new JsonException($"{where} is not valid Unicode (a lone surrogate)")
                    : new ArgumentException($"{where}: not valid Unicode (a lone surrogate)");
        }
        return s;
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
                    if (!map.TryAdd(Text(p.Name, "a key", read: true), ToValue(p.Value)))
                        throw new JsonException($"duplicate JSON key '{p.Name}'");
                return map;
            case JsonValueKind.Array:
                return e.EnumerateArray().Select(ToValue).ToList();
            case JsonValueKind.String:
                return Text(e.GetString()!, "a string", read: true);
            case JsonValueKind.True:
                return true;
            case JsonValueKind.False:
                return false;
            case JsonValueKind.Number:
                if (e.GetRawText().AsSpan().IndexOfAny(".eE") < 0)
                    return e.TryGetInt64(out long l) ? l : throw new JsonException("an integer is outside the signed 64-bit range");
                double d = e.GetDouble();
                return double.IsFinite(d) ? d : throw new JsonException($"a number overflows a double: {e.GetRawText()}");
            default:
                return null;
        }
    }

    private static readonly byte[] GuidTail = Convert.FromHexString("000000001000800000AA00389B71");

    private static int WavBits(string? format) => format switch
    {
        "u8" => 8,
        "i16" => 16,
        "i24" => 24,
        "i32" or "f32" => 32,
        "f64" => 64,
        _ => 0,
    };

    /// <summary>Writes one real signal as a mono WAV file (conventions: Signal files, WAV).</summary>
    /// <param name="path">The file to write.</param>
    /// <param name="signal">The signal; only its samples and sample rate are stored.</param>
    /// <param name="sampleFormat"><c>u8</c>, <c>i16</c>, <c>i24</c>, <c>i32</c> (PCM), <c>f32</c> or <c>f64</c> (IEEE float).</param>
    public static void WriteWav(string path, Signal<double> signal, string sampleFormat = "f32")
    {
        ArgumentNullException.ThrowIfNull(signal);
        WriteWav(path, [signal], sampleFormat);
    }

    /// <summary>Writes real signals, one per channel, as a PCM or IEEE float WAV file (conventions: Signal files, WAV).
    /// Only the samples and the sample rate are stored.</summary>
    /// <param name="path">The file to write.</param>
    /// <param name="channels">One or more signals with the same length and the same whole-number sample rate.</param>
    /// <param name="sampleFormat"><c>u8</c>, <c>i16</c>, <c>i24</c>, <c>i32</c> (PCM), <c>f32</c> or <c>f64</c> (IEEE float).</param>
    public static void WriteWav(string path, IReadOnlyList<Signal<double>> channels, string sampleFormat = "f32")
    {
        ArgumentException.ThrowIfNullOrEmpty(path);
        ArgumentNullException.ThrowIfNull(channels);
        int bits = WavBits(sampleFormat);
        if (bits == 0)
            throw new ArgumentException($"unknown WAV sample format '{sampleFormat}'", nameof(sampleFormat));
        if (channels.Count == 0 || channels.Any(s => s is null))
            throw new ArgumentException("channels must be one signal or a non-empty list of them", nameof(channels));
        double rate = channels[0].SampleRate;
        int n = channels[0].Length, nch = channels.Count, w = bits / 8;
        if (channels.Any(s => s.SampleRate != rate || s.Length != n))
            throw new ArgumentException("every channel must have the same sample rate and length", nameof(channels));
        if (rate != Math.Floor(rate) || rate > uint.MaxValue)
            throw new ArgumentException("the sample rate must be a whole number of hertz below 2^32", nameof(channels));
        bool isFloat = sampleFormat[0] == 'f';
        long block = (long)nch * w;
        if (block > ushort.MaxValue)
            throw new ArgumentException("too many channels: the block align must fit 16 bits", nameof(channels));
        if ((long)rate * block > uint.MaxValue)
            throw new ArgumentException("the byte rate (sample rate x block align) must fit 32 bits", nameof(channels));
        long nbytes = n * block;
        long riffSize = 4 + (isFloat ? 38 : 24) + 8 + nbytes + nbytes % 2;
        if (riffSize > uint.MaxValue)
            throw new ArgumentException("too many samples for a WAV file", nameof(channels));
        var data = new byte[checked((int)nbytes)];
        double scale = Math.ScaleB(1.0, bits - 1);
        for (int c = 0; c < nch; c++)
        {
            ReadOnlySpan<double> x = channels[c].Samples;
            for (int i = 0; i < n; i++)
            {
                Span<byte> b = data.AsSpan((i * nch + c) * w, w);
                double v = x[i];
                if (isFloat)
                {
                    if (bits == 64) BinaryPrimitives.WriteDoubleLittleEndian(b, v);
                    else BinaryPrimitives.WriteSingleLittleEndian(b, (float)v);
                    continue;
                }
                if (!double.IsFinite(v))
                    throw new ArgumentException($"{sampleFormat} cannot hold non-finite samples", nameof(channels));
                double code = Math.Round(v * scale, MidpointRounding.ToEven);
                if (code < -scale || code > scale - 1)
                    throw new ArgumentException($"a sample is outside the range of {sampleFormat} (full scale is 1.0)", nameof(channels));
                int k = (int)code;
                switch (bits)
                {
                    case 8: b[0] = (byte)(k + 128); break;
                    case 16: BinaryPrimitives.WriteInt16LittleEndian(b, (short)k); break;
                    case 24: b[0] = (byte)k; b[1] = (byte)(k >> 8); b[2] = (byte)(k >> 16); break;
                    default: BinaryPrimitives.WriteInt32LittleEndian(b, k); break;
                }
            }
        }
        using var ms = new MemoryStream();
        using (var bw = new BinaryWriter(ms, System.Text.Encoding.ASCII, leaveOpen: true))
        {
            bw.Write("RIFF"u8);
            bw.Write((uint)riffSize);
            bw.Write("WAVE"u8);
            bw.Write("fmt "u8);
            bw.Write(isFloat ? 18 : 16);
            bw.Write((ushort)(isFloat ? 3 : 1));
            bw.Write((ushort)nch);
            bw.Write((uint)rate);
            bw.Write((uint)(rate * block));
            bw.Write((ushort)block);
            bw.Write((ushort)bits);
            if (isFloat)
            {
                bw.Write((ushort)0);
                bw.Write("fact"u8);
                bw.Write(4);
                bw.Write((uint)n);
            }
            bw.Write("data"u8);
            bw.Write((uint)nbytes);
            bw.Write(data);
            if (nbytes % 2 == 1)
                bw.Write((byte)0);
        }
        File.WriteAllBytes(path, ms.ToArray());
    }

    /// <summary>Reads a PCM or IEEE float WAV file as real signals, one per channel, in units <c>"FS"</c>
    /// (conventions: Signal files, WAV).</summary>
    /// <param name="path">The file to read.</param>
    /// <returns>One signal per channel, all with the file's sample rate.</returns>
    /// <exception cref="ArgumentException">The file is not a WAV file this reads exactly.</exception>
    public static Signal<double>[] ReadWav(string path)
    {
        ArgumentException.ThrowIfNullOrEmpty(path);
        byte[] raw = File.ReadAllBytes(path);
        ArgumentException Bad(string message) => new(message, nameof(path));
        if (raw.Length < 12 || !raw.AsSpan(0, 4).SequenceEqual("RIFF"u8) || !raw.AsSpan(8, 4).SequenceEqual("WAVE"u8))
            throw Bad("not a RIFF WAVE file");
        long pos = 12;
        byte[]? fmt = null;
        int dataStart, dataLength;
        while (true)
        {
            if (pos + 8 > raw.Length)
                throw Bad(fmt is null ? "no fmt chunk" : "no data chunk");
            ReadOnlySpan<byte> id = raw.AsSpan((int)pos, 4);
            uint size = BinaryPrimitives.ReadUInt32LittleEndian(raw.AsSpan((int)pos + 4, 4));
            long start = pos + 8, end = start + size;
            if (end > raw.Length)
                throw Bad($"the '{System.Text.Encoding.Latin1.GetString(id)}' chunk runs past the end of the file");
            if (id.SequenceEqual("data"u8))
            {
                if (fmt is null)
                    throw Bad("the fmt chunk must come before the data chunk");
                (dataStart, dataLength) = ((int)start, (int)size);
                break;
            }
            if (id.SequenceEqual("fmt "u8) && fmt is null)
                fmt = raw[(int)start..(int)end];
            pos = end + size % 2;
        }
        if (fmt.Length < 16)
            throw Bad("the fmt chunk is shorter than 16 bytes");
        int tag = BinaryPrimitives.ReadUInt16LittleEndian(fmt);
        int nch = BinaryPrimitives.ReadUInt16LittleEndian(fmt.AsSpan(2));
        uint rate = BinaryPrimitives.ReadUInt32LittleEndian(fmt.AsSpan(4));
        int block = BinaryPrimitives.ReadUInt16LittleEndian(fmt.AsSpan(12));
        int bits = BinaryPrimitives.ReadUInt16LittleEndian(fmt.AsSpan(14));
        if (tag == 0xFFFE)
        {
            if (fmt.Length < 40)
                throw Bad("an extensible fmt chunk needs at least 40 bytes");
            ReadOnlySpan<byte> guid = fmt.AsSpan(24, 16);
            if (!guid[2..].SequenceEqual(GuidTail) || guid[1] != 0 || guid[0] is not (1 or 3))
                throw Bad("the extensible sub-format is not PCM or IEEE float");
            tag = guid[0];
        }
        if (tag is not (1 or 3))
            throw Bad($"WAV format {tag} is not PCM or IEEE float");
        if (tag == 1 ? bits is not (8 or 16 or 24 or 32) : bits is not (32 or 64))
            throw Bad($"{bits}-bit {(tag == 1 ? "PCM" : "float")} is not supported");
        if (nch < 1 || rate < 1)
            throw Bad("a WAV file needs at least one channel and a sample rate of at least 1");
        if (block != nch * bits / 8)
            throw Bad($"block align {block} does not match {nch} channels of {bits} bits");
        if (dataLength % block != 0)
            throw Bad($"{dataLength} data bytes is not a whole number of {block}-byte frames");
        int w = bits / 8, frames = dataLength / block;
        double scale = Math.ScaleB(1.0, bits - 1);
        var result = new Signal<double>[nch];
        var x = new double[frames];
        for (int c = 0; c < nch; c++)
        {
            for (int i = 0; i < frames; i++)
            {
                ReadOnlySpan<byte> b = raw.AsSpan(dataStart + (i * nch + c) * w, w);
                x[i] = (tag, bits) switch
                {
                    (3, 32) => BinaryPrimitives.ReadSingleLittleEndian(b),
                    (3, _) => BinaryPrimitives.ReadDoubleLittleEndian(b),
                    (_, 8) => (b[0] - 128) / scale,
                    (_, 16) => BinaryPrimitives.ReadInt16LittleEndian(b) / scale,
                    (_, 24) => (b[0] | b[1] << 8 | (sbyte)b[2] << 16) / scale,
                    _ => BinaryPrimitives.ReadInt32LittleEndian(b) / scale,
                };
            }
            result[c] = new Signal<double>(x, rate, units: "FS");
        }
        return result;
    }

    private static readonly byte[] NpyMagic = [0x93, (byte)'N', (byte)'U', (byte)'M', (byte)'P', (byte)'Y'];

    /// <summary>Writes a real array as a NumPy <c>.npy</c> file of <c>'&lt;f8'</c>, in the layout <c>numpy.save</c>
    /// writes (conventions: Signal files, NumPy .npy).</summary>
    /// <param name="path">The file to write.</param>
    /// <param name="x">The values, NaN and infinities included.</param>
    public static void WriteNpy(string path, ReadOnlySpan<double> x)
    {
        ArgumentException.ThrowIfNullOrEmpty(path);
        WriteNpyFile(path, "<f8", x.Length, MemoryMarshal.AsBytes(x));
    }

    /// <summary>Writes a complex array as a NumPy <c>.npy</c> file of <c>'&lt;c16'</c>, in the layout <c>numpy.save</c>
    /// writes (conventions: Signal files, NumPy .npy).</summary>
    /// <param name="path">The file to write.</param>
    /// <param name="x">The values, real then imaginary part of each.</param>
    public static void WriteNpy(string path, ReadOnlySpan<Complex> x)
    {
        ArgumentException.ThrowIfNullOrEmpty(path);
        WriteNpyFile(path, "<c16", x.Length, MemoryMarshal.AsBytes(x));
    }

    private static void WriteNpyFile(string path, string descr, int n, ReadOnlySpan<byte> native)
    {
        string text = string.Create(CultureInfo.InvariantCulture, $"{{'descr': '{descr}', 'fortran_order': False, 'shape': ({n},), }}");
        byte[] file = new byte[128 + native.Length];
        NpyMagic.CopyTo(file, 0);
        file[6] = 1;
        BinaryPrimitives.WriteUInt16LittleEndian(file.AsSpan(8), 118);
        System.Text.Encoding.ASCII.GetBytes(text.PadRight(117) + "\n", file.AsSpan(10));
        Span<byte> data = file.AsSpan(128);
        native.CopyTo(data);
        if (!BitConverter.IsLittleEndian)
        {
            Span<long> words = MemoryMarshal.Cast<byte, long>(data);
            BinaryPrimitives.ReverseEndianness(words, words);
        }
        File.WriteAllBytes(path, file);
    }

    /// <summary>Reads a 1-D <c>'&lt;f8'</c> or <c>'&lt;c16'</c> NumPy <c>.npy</c> file, versions 1.0 to 3.0
    /// (conventions: Signal files, NumPy .npy). The header is parsed, never evaluated.</summary>
    /// <typeparam name="T"><see cref="double"/> for <c>'&lt;f8'</c>, <see cref="Complex"/> for <c>'&lt;c16'</c>.</typeparam>
    /// <param name="path">The file to read.</param>
    /// <returns>The values.</returns>
    /// <exception cref="ArgumentException">The file is not a <c>.npy</c> file of <typeparamref name="T"/> this reads.</exception>
    public static T[] ReadNpy<T>(string path) where T : struct
    {
        ArgumentException.ThrowIfNullOrEmpty(path);
        bool wantComplex = typeof(T) == typeof(Complex);
        if (!wantComplex && typeof(T) != typeof(double))
            throw new ArgumentException($"the element type must be double or Complex, not {typeof(T).Name}", nameof(T));
        byte[] raw = File.ReadAllBytes(path);
        ArgumentException Bad(string message) => new(message, nameof(path));
        if (raw.Length < 8 || !raw.AsSpan(0, 6).SequenceEqual(NpyMagic))
            throw Bad("not a .npy file");
        int width = (raw[6], raw[7]) switch
        {
            (1, 0) => 2,
            (2, 0) or (3, 0) => 4,
            _ => throw Bad($".npy version {raw[6]}.{raw[7]} is not supported"),
        };
        if (raw.Length < 8 + width)
            throw Bad("the .npy file ends inside its header length");
        long size = width == 2 ? BinaryPrimitives.ReadUInt16LittleEndian(raw.AsSpan(8)) : BinaryPrimitives.ReadUInt32LittleEndian(raw.AsSpan(8));
        long start = 8 + width + size;
        if (start > raw.Length)
            throw Bad("the .npy header runs past the end of the file");
        ReadOnlySpan<byte> head = raw.AsSpan(8 + width, (int)size);
        if (head.ContainsAnyInRange((byte)128, (byte)255))
            throw Bad("the .npy header must be ASCII");
        Dictionary<string, object> d = new NpyHeader(System.Text.Encoding.ASCII.GetString(head), Bad).Parse();
        if (d.Count != 3 || !d.TryGetValue("descr", out object? descr) || !d.TryGetValue("fortran_order", out object? order)
            || !d.TryGetValue("shape", out object? shapeValue))
            throw Bad("the .npy header needs exactly descr, fortran_order and shape");
        if (descr is not ("<f8" or "<c16"))
            throw Bad($"only '<f8' and '<c16' arrays are read, not {descr}");
        if (order is not bool)
            throw Bad("fortran_order must be True or False");
        if (shapeValue is not long[] { Length: 1 } shape)
            throw Bad("only 1-D arrays are read");
        bool isComplex = (string)descr == "<c16";
        if (isComplex != wantComplex)
            throw Bad($"the file holds {(isComplex ? "complex" : "real")} values, not {typeof(T).Name}");
        int itemSize = isComplex ? 16 : 8;
        long bytes = raw.Length - start;
        if (bytes % itemSize != 0 || bytes / itemSize != shape[0])
            throw Bad(string.Create(CultureInfo.InvariantCulture, $"{bytes} data bytes do not match shape ({shape[0]},)"));
        T[] result = new T[bytes / itemSize];
        Span<byte> data = MemoryMarshal.AsBytes(result.AsSpan());
        raw.AsSpan((int)start).CopyTo(data);
        if (!BitConverter.IsLittleEndian)
        {
            Span<long> words = MemoryMarshal.Cast<byte, long>(data);
            BinaryPrimitives.ReverseEndianness(words, words);
        }
        return result;
    }

    /// <summary>The header grammar of conventions: Signal files, NumPy .npy. Values are strings, bools and
    /// <c>long[]</c> tuples.</summary>
    private sealed class NpyHeader(string s, Func<string, ArgumentException> bad)
    {
        private int _i;

        private ArgumentException Fail() => bad(string.Create(CultureInfo.InvariantCulture, $"the .npy header is not a dict this reader accepts (at {_i})"));

        private char Peek()
        {
            while (_i < s.Length && s[_i] is ' ' or '\t' or '\r' or '\n')
                _i++;
            return _i < s.Length ? s[_i] : '\0';
        }

        private void Take(char c)
        {
            if (Peek() != c || _i >= s.Length)
                throw Fail();
            _i++;
        }

        private string String()
        {
            char q = Peek();
            int j = q is '\'' or '"' ? s.IndexOf(q, _i + 1) : -1;
            if (j < 0 || s.AsSpan(_i + 1, j - _i - 1).Contains('\\'))
                throw Fail();
            string v = s[(_i + 1)..j];
            _i = j + 1;
            return v;
        }

        private long Integer()
        {
            Peek();
            int j = _i;
            long v = 0;
            while (j < s.Length && char.IsAsciiDigit(s[j]))
            {
                int digit = s[j] - '0';
                if (v > (long.MaxValue - digit) / 10)
                    throw bad("a .npy shape is too large");
                v = v * 10 + digit;
                j++;
            }
            if (j == _i || (j - _i > 1 && s[_i] == '0'))
                throw Fail();
            _i = j;
            return v;
        }

        private object Value()
        {
            char c = Peek();
            if (c is '\'' or '"')
                return String();
            if (c == '(')
            {
                _i++;
                List<long> items = [];
                bool trailing = false;
                while (Peek() != ')')
                {
                    items.Add(Integer());
                    trailing = Peek() == ',';
                    if (trailing)
                        _i++;
                    else if (Peek() != ')')
                        throw Fail();
                }
                Take(')');
                if (items.Count == 1 && !trailing)
                    throw Fail();
                return items.ToArray();
            }
            foreach (string word in (string[])["True", "False"])
            {
                if (string.CompareOrdinal(s, _i, word, 0, word.Length) == 0)
                {
                    _i += word.Length;
                    return word == "True";
                }
            }
            throw Fail();
        }

        public Dictionary<string, object> Parse()
        {
            Dictionary<string, object> d = new(StringComparer.Ordinal);
            Take('{');
            while (Peek() != '}')
            {
                if (_i >= s.Length)
                    throw Fail();
                string key = String();
                Take(':');
                if (d.ContainsKey(key))
                    throw bad($"the .npy header has '{key}' twice");
                d[key] = Value();
                if (Peek() == ',')
                    _i++;
                else if (Peek() != '}')
                    throw Fail();
            }
            Take('}');
            Peek();
            if (_i < s.Length)
                throw Fail();
            return d;
        }
    }
}
