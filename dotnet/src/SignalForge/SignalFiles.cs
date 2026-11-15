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

    /// <summary>Most channels in one SigMF recording (<c>core:num_channels</c>).</summary>
    public const int MaxChannels = 65535;

    private static readonly HashSet<string> Reserved =
    [
        "core:datatype", "core:version", "core:sample_rate", "core:extensions",
        "core:num_channels", "core:dataset", "core:metadata_only",
    ];

    private const string AnnotationsKey = "core:annotations";

    private readonly record struct Format(bool IsComplex, bool IsInteger, int Bits, bool BigEndian, bool Unsigned)
    {
        public int PartBytes => Bits / 8;

        // the byte holding the top bit, which offset binary flips (ADR 0058)
        public int TopByte => BigEndian ? 0 : PartBytes - 1;
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
            int bits = body switch
            {
                "f64" => 64,
                "f32" or "i32" or "u32" => 32,
                "f16" or "i16" or "u16" => 16,
                "i8" or "u8" => 8,
                _ => 0,
            };
            bool orderOk = bits == 8 ? us < 0 : order is "le" or "be";
            if (bits > 0 && orderOk)
                return new Format(datatype[0] == 'c', body[0] != 'f', bits, order == "be", body[0] == 'u');
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
                // (Half)v rounds once from the double, never through float (ADR 0087)
                switch (f.Bits)
                {
                    case 64 when f.BigEndian: BinaryPrimitives.WriteDoubleBigEndian(b, v); break;
                    case 64: BinaryPrimitives.WriteDoubleLittleEndian(b, v); break;
                    case 32 when f.BigEndian: BinaryPrimitives.WriteSingleBigEndian(b, (float)v); break;
                    case 32: BinaryPrimitives.WriteSingleLittleEndian(b, (float)v); break;
                    case 16 when f.BigEndian: BinaryPrimitives.WriteHalfBigEndian(b, (Half)v); break;
                    default: BinaryPrimitives.WriteHalfLittleEndian(b, (Half)v); break;
                }
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
            if (f.Unsigned)
                b[f.TopByte] ^= 0x80;
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
        Span<byte> flipped = stackalloc byte[8];
        for (int i = 0; i < parts.Length; i++)
        {
            scoped ReadOnlySpan<byte> b = data.Slice(i * w, w);
            if (f.Unsigned)
            {
                // offset binary is the signed code with its top bit flipped (ADR 0058)
                b.CopyTo(flipped);
                flipped[f.TopByte] ^= 0x80;
                b = flipped[..w];
            }
            parts[i] = (f.IsInteger, f.Bits, f.BigEndian) switch
            {
                (false, 64, true) => BinaryPrimitives.ReadDoubleBigEndian(b),
                (false, 64, false) => BinaryPrimitives.ReadDoubleLittleEndian(b),
                (false, 32, true) => BinaryPrimitives.ReadSingleBigEndian(b),
                (false, 32, false) => BinaryPrimitives.ReadSingleLittleEndian(b),
                (false, _, true) => (double)BinaryPrimitives.ReadHalfBigEndian(b),
                (false, _, false) => (double)BinaryPrimitives.ReadHalfLittleEndian(b),
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
        WriteSigmfChannels(path, [signal], datatype);
    }

    /// <summary>Writes <paramref name="channels"/>, one signal per channel, as one interleaved SigMF recording.</summary>
    /// <typeparam name="T"><c>double</c> or <see cref="Complex"/>.</typeparam>
    /// <param name="path">The base path, or either file's name.</param>
    /// <param name="channels">1 to <see cref="MaxChannels"/> signals of one length whose sample rate, center
    /// frequency, time origin, units, impedance and metadata are identical.</param>
    /// <param name="datatype">The sample datatype; null for <c>cf64_le</c> or <c>rf64_le</c>, which lose nothing.</param>
    public static void WriteSigmfChannels<T>(string path, IReadOnlyList<Signal<T>> channels, string? datatype = null)
        where T : struct
    {
        ArgumentNullException.ThrowIfNull(channels);
        int count = channels.Count;
        if (count is < 1 or > MaxChannels)
            throw new ArgumentException($"a recording needs 1 to {MaxChannels} channels, not {count}", nameof(channels));
        foreach (var s in channels)
            ArgumentNullException.ThrowIfNull(s, nameof(channels));
        int length = channels[0].Length;
        if (channels.Any(s => s.Length != length))
            throw new ArgumentException("the channels must have the same number of samples", nameof(channels));
        if ((long)length * count > Array.MaxLength)
            throw new ArgumentException("the channels hold too many samples for one array", nameof(channels));
        bool isComplex = typeof(T) == typeof(Complex);
        datatype ??= isComplex ? "cf64_le" : "rf64_le";
        var f = Parse(datatype, nameof(datatype));
        CheckKind<T>(f, datatype, nameof(datatype));
        var frames = new T[length * count];
        for (int c = 0; c < count; c++)
        {
            var x = channels[c].Samples;
            for (int k = 0; k < length; k++)
                frames[k * count + c] = x[k];
        }
        byte[] data = isComplex
            ? EncodeSamples(MemoryMarshal.Cast<T, Complex>(frames.AsSpan()), datatype)
            : EncodeSamples(MemoryMarshal.Cast<T, double>(frames.AsSpan()), datatype);
        byte[] meta = SigmfMeta(channels[0], datatype, count);
        for (int c = 1; c < count; c++)
            if (!SigmfMeta(channels[c], datatype, count).AsSpan().SequenceEqual(meta))
                throw new ArgumentException(
                    "the channels must have the same sample rate, center frequency, time origin, units, impedance and metadata",
                    nameof(channels));
        var (metaPath, dataPath) = Files(path);
        File.WriteAllBytes(dataPath, data);
        File.WriteAllBytes(metaPath, meta);
    }

    /// <summary>Writes <paramref name="segments"/> as one one-channel SigMF recording with one capture per segment, the
    /// inverse of <see cref="ReadSigmfCaptures{T}"/> (conventions: Signal files, Captures; ADR 0100).</summary>
    /// <typeparam name="T"><c>double</c> or <see cref="Complex"/>.</typeparam>
    /// <param name="path">The base path, or either file's name.</param>
    /// <param name="segments">One or more signals, only the last of which may be empty. Each later time origin must be
    /// exactly the first's plus <c>start / sample_rate</c>; the sample rate, units, impedance and metadata other than
    /// annotations must be identical.</param>
    /// <param name="datatype">The sample datatype; null for <c>cf64_le</c> or <c>rf64_le</c>, which lose nothing.</param>
    public static void WriteSigmfCaptures<T>(string path, IReadOnlyList<Signal<T>> segments, string? datatype = null)
        where T : struct
    {
        ArgumentNullException.ThrowIfNull(segments);
        if (segments.Count == 0)
            throw new ArgumentException("segments must be a non-empty list of signals", nameof(segments));
        foreach (var s in segments)
            ArgumentNullException.ThrowIfNull(s, nameof(segments));
        for (int j = 0; j < segments.Count - 1; j++)
            if (segments[j].Length == 0)
                throw new ArgumentException("only the last segment may be empty", nameof(segments));
        if (segments.Sum(s => (long)s.Length) > Array.MaxLength)
            throw new ArgumentException("the segments hold too many samples for one array", nameof(segments));
        bool isComplex = typeof(T) == typeof(Complex);
        datatype ??= isComplex ? "cf64_le" : "rf64_le";
        var f = Parse(datatype, nameof(datatype));
        CheckKind<T>(f, datatype, nameof(datatype));
        var first = segments[0];
        double t0 = Check.Finite(first.TimeOrigin, nameof(segments));
        var empty = new SigmfLayout(0.0, [], []);
        byte[] shared = SigmfMeta(first, datatype, 1, empty);
        var captures = new List<(long Start, double Frequency)>();
        var annotations = new List<object?>();
        long start = 0;
        for (int j = 0; j < segments.Count; j++)
        {
            var s = segments[j];
            if (j > 0 && !SigmfMeta(s, datatype, 1, empty).AsSpan().SequenceEqual(shared))
                throw new ArgumentException(
                    "the segments must have the same sample rate, units, impedance and metadata apart from annotations",
                    nameof(segments));
            double origin = t0 + start / first.SampleRate;
            if (j > 0 && s.TimeOrigin != origin)
                throw new ArgumentException(
                    FormattableString.Invariant($"segment {j} must have time origin {origin:R} (the first's plus {start} / sample_rate), not {s.TimeOrigin:R}"),
                    nameof(segments));
            bool last = j == segments.Count - 1;
            if (s.Metadata.TryGetValue(AnnotationsKey, out var mine))
            {
                foreach (IDictionary a in (IEnumerable)mine!)
                {
                    long at = SampleIndex(a["core:sample_start"], AnnotationsKey);
                    if (!last && at >= s.Length)
                        throw new ArgumentException($"an annotation of segment {j} starts past its {s.Length} samples", nameof(segments));
                    var moved = new Dictionary<string, object?>();
                    foreach (DictionaryEntry e in a)
                        moved[e.Key as string ?? throw new ArgumentException("annotation keys must be strings", nameof(segments))] = e.Value;
                    moved["core:sample_start"] = at + start;
                    annotations.Add(moved);
                }
            }
            captures.Add((start, Check.Finite(s.CenterFrequency, nameof(segments))));
            start += s.Length;
        }
        var samples = new T[start];
        int k = 0;
        foreach (var s in segments)
        {
            s.Samples.CopyTo(samples.AsSpan(k));
            k += s.Length;
        }
        byte[] data = isComplex
            ? EncodeSamples(MemoryMarshal.Cast<T, Complex>(samples.AsSpan()), datatype)
            : EncodeSamples(MemoryMarshal.Cast<T, double>(samples.AsSpan()), datatype);
        byte[] meta = SigmfMeta(first, datatype, 1, new SigmfLayout(t0, captures, annotations));
        var (metaPath, dataPath) = Files(path);
        File.WriteAllBytes(dataPath, data);
        File.WriteAllBytes(metaPath, meta);
    }

    /// <summary>A time origin, captures and annotations that replace a signal's own in <see cref="SigmfMeta"/>.</summary>
    private sealed record SigmfLayout(double TimeOrigin, List<(long Start, double Frequency)> Captures, List<object?> Annotations);

    /// <summary>The <c>.sigmf-meta</c> bytes for <paramref name="signal"/>, one of <paramref name="channels"/>, checked;
    /// <paramref name="layout"/> replaces its time origin, captures and annotations (its own are still checked).</summary>
    private static byte[] SigmfMeta<T>(Signal<T> signal, string datatype, int channels, SigmfLayout? layout = null) where T : struct
    {
        if (layout is null)
        {
            Check.Finite(signal.TimeOrigin, nameof(signal));
            Check.Finite(signal.CenterFrequency, nameof(signal));
        }
        object? annotations = signal.Metadata.TryGetValue(AnnotationsKey, out var av) ? av : new List<object?>();
        CheckAnnotations(annotations, $"metadata {AnnotationsKey}");
        if (layout is not null)
            annotations = layout.Annotations;

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
            if (channels > 1)
                w.WriteNumber("core:num_channels", channels);
            w.WriteStartArray("core:extensions");
            w.WriteStartObject();
            w.WriteString("name", "signalforge");
            w.WriteString("version", "1.0.0");
            w.WriteBoolean("optional", true);
            w.WriteEndObject();
            w.WriteEndArray();
            w.WritePropertyName("signalforge:time_origin");
            WriteDouble(w, layout?.TimeOrigin ?? signal.TimeOrigin);
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
            foreach (var (k, v) in signal.Metadata.Where(kv => kv.Key.Contains(':', StringComparison.Ordinal) && kv.Key != AnnotationsKey))
            {
                if (Reserved.Contains(k) || k.StartsWith("signalforge:", StringComparison.Ordinal))
                    throw new ArgumentException($"metadata key '{k}' is reserved", nameof(signal));
                w.WritePropertyName(Text(k, k));
                WriteValue(w, v, k, 3);
            }
            w.WriteEndObject();
            w.WriteStartArray("captures");
            foreach (var (start, frequency) in layout?.Captures ?? [(0, signal.CenterFrequency)])
            {
                w.WriteStartObject();
                w.WriteNumber("core:sample_start", start);
                w.WritePropertyName("core:frequency");
                WriteDouble(w, frequency);
                w.WriteEndObject();
            }
            w.WriteEndArray();
            w.WritePropertyName("annotations");
            WriteValue(w, annotations, AnnotationsKey, 2);
            w.WriteEndObject();
        }
        buffer.WriteByte((byte)'\n');
        return buffer.ToArray();
    }

    /// <summary>Checks <paramref name="v"/> as a SigMF annotations list (conventions: Signal files, Annotations).</summary>
    private static void CheckAnnotations(object? v, string what)
    {
        if (v is not IEnumerable items || v is string or IDictionary)
            throw new ArgumentException($"{what} must be a JSON array");
        long last = 0;
        int i = 0;
        foreach (object? a in items)
        {
            if (a is not IDictionary map)
                throw new ArgumentException($"{what}[{i}] must be a JSON object");
            long start = SampleIndex(map["core:sample_start"], $"{what}[{i}] core:sample_start");
            if (map.Contains("core:sample_count"))
                SampleIndex(map["core:sample_count"], $"{what}[{i}] core:sample_count");
            if (start < last)
                throw new ArgumentException($"{what} must be sorted by core:sample_start");
            last = start;
            i++;
        }
    }

    /// <summary>An annotation's integer field, which must be at least 0.</summary>
    private static long SampleIndex(object? n, string what)
    {
        long? k = n switch
        {
            sbyte or byte or short or ushort or int or uint or long => Convert.ToInt64(n, CultureInfo.InvariantCulture),
            ulong u when u <= long.MaxValue => (long)u,
            _ => null,
        };
        return k is >= 0 ? k.Value : throw new ArgumentException($"{what} must be an integer >= 0");
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
    public static Signal<T> ReadSigmf<T>(string path) where T : struct => ReadSigmfCore<T>(path, SigmfRead.One)[0];

    /// <summary>Reads a SigMF recording of any number of channels as one signal per channel.</summary>
    /// <typeparam name="T"><c>double</c> for a real recording, <see cref="Complex"/> for a complex one.</typeparam>
    /// <param name="path">The base path, or either file's name.</param>
    /// <exception cref="ArgumentException">The recording is malformed or of the other kind.</exception>
    /// <exception cref="IOException">A file is missing or unreadable.</exception>
    public static IReadOnlyList<Signal<T>> ReadSigmfChannels<T>(string path) where T : struct =>
        ReadSigmfCore<T>(path, SigmfRead.Channels);

    /// <summary>Reads a one-channel SigMF recording as one signal per capture, each with its capture's center
    /// frequency and a time origin moved to the capture's first sample.</summary>
    /// <typeparam name="T"><c>double</c> for a real recording, <see cref="Complex"/> for a complex one.</typeparam>
    /// <param name="path">The base path, or either file's name.</param>
    /// <exception cref="ArgumentException">The recording is malformed or of the other kind.</exception>
    /// <exception cref="IOException">A file is missing or unreadable.</exception>
    public static IReadOnlyList<Signal<T>> ReadSigmfCaptures<T>(string path) where T : struct =>
        ReadSigmfCore<T>(path, SigmfRead.Captures);

    private enum SigmfRead
    {
        One,
        Channels,
        Captures,
    }

    private static List<Signal<T>> ReadSigmfCore<T>(string path, SigmfRead mode) where T : struct
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
        object? nc = glob.TryGetValue("core:num_channels", out var ncv) ? ncv : 1L;
        if (mode != SigmfRead.Channels && nc is not 1L)
            throw new ArgumentException(
                $"{(mode == SigmfRead.One ? "ReadSigmf" : "ReadSigmfCaptures")} reads one channel; ReadSigmfChannels reads more",
                nameof(path));
        if (nc is not long count || count is < 1 or > MaxChannels)
            throw new ArgumentException($"core:num_channels must be a whole number from 1 to {MaxChannels}", nameof(path));
        foreach (string k in (string[])["core:dataset", "core:metadata_only"])
            if (glob.ContainsKey(k))
                throw new ArgumentException($"{k} recordings are not supported", nameof(path));
        object? captures = top.TryGetValue("captures", out var cv) ? cv : new List<object?>();
        if (captures is not List<object?> caps)
            throw new ArgumentException("captures must be a JSON array", nameof(path));
        var freqs = new List<double>();
        var starts = new List<long>();
        for (int i = 0; i < caps.Count; i++)
        {
            var c = Obj(caps[i], $"captures[{i}]");
            if (c.TryGetValue("core:header_bytes", out var hb) && hb is not 0L)
                throw new ArgumentException("captures with header bytes are not supported", nameof(path));
            freqs.Add(c.TryGetValue("core:frequency", out var fq) ? Num(fq, $"captures[{i}] core:frequency") : 0.0);
            if (mode == SigmfRead.Captures)
                starts.Add(c.GetValueOrDefault("core:sample_start") is long s && s >= 0
                    ? s
                    : throw new ArgumentException($"captures[{i}] core:sample_start must be an integer, at least 0", nameof(path)));
        }
        if (mode != SigmfRead.Captures && freqs.Distinct().Count() > 1)
            throw new ArgumentException(
                "captures at different frequencies are not one signal; ReadSigmfCaptures reads them", nameof(path));
        if (glob.ContainsKey(AnnotationsKey))
            throw new ArgumentException($"{AnnotationsKey} belongs at the top level, not in global", nameof(path));
        object? annotations = top.TryGetValue("annotations", out var av) ? av : new List<object?>();
        CheckAnnotations(annotations, "annotations");
        object? units = glob.GetValueOrDefault("signalforge:units");
        if (units is not (null or string))
            throw new ArgumentException("signalforge:units must be a string", nameof(path));
        object? impedance = glob.GetValueOrDefault("signalforge:impedance");
        var metadata = new Dictionary<string, object?>(
            Obj(glob.TryGetValue("signalforge:metadata", out var mv) ? mv : new Dictionary<string, object?>(), "signalforge:metadata"));
        foreach (var (k, v) in glob)
            if (!Reserved.Contains(k) && !k.StartsWith("signalforge:", StringComparison.Ordinal))
                metadata[k] = v;
        if (annotations is List<object?> { Count: > 0 })
            metadata[AnnotationsKey] = annotations;
        double timeOrigin = glob.TryGetValue("signalforge:time_origin", out var t0) ? Num(t0, "signalforge:time_origin") : 0.0;
        double frequency = freqs.Count > 0 ? freqs[0] : 0.0;
        double? ohms = impedance is null ? null : Num(impedance, "signalforge:impedance");
        T[] samples = DecodeSamples<T>(File.ReadAllBytes(dataPath), datatype);
        if (mode == SigmfRead.Captures)
            return Segments(samples, starts, freqs, (List<object?>)annotations!, metadata,
                s => new(s.Samples, rate, s.Frequency, timeOrigin + s.Start / rate, (string?)units, ohms, s.Metadata));
        int n = (int)count;
        if (samples.Length % n != 0)
            throw new ArgumentException($"{samples.Length} samples is not a whole number of {n}-channel frames", nameof(path));
        var result = new List<Signal<T>>(n);
        for (int ch = 0; ch < n; ch++)
        {
            var x = new T[samples.Length / n];
            for (int k = 0; k < x.Length; k++)
                x[k] = samples[k * n + ch];
            result.Add(new Signal<T>(x, rate, frequency, timeOrigin, (string?)units, ohms,
                (Dictionary<string, object?>)Copy(metadata)!));
        }
        return result;
    }

    /// <summary>Splits a recording's samples at its capture starts (conventions: Signal files, Captures).</summary>
    private static List<Signal<T>> Segments<T>(T[] samples, List<long> starts, List<double> freqs, List<object?> annotations,
        Dictionary<string, object?> metadata, Func<(T[] Samples, long Start, double Frequency, Dictionary<string, object?> Metadata), Signal<T>> make)
        where T : struct
    {
        if (starts.Count == 0)
            (starts, freqs) = ([0], [0.0]);
        if (starts[0] != 0)
            throw new ArgumentException("the first capture must start at sample 0");
        for (int j = 1; j < starts.Count; j++)
            if (starts[j] <= starts[j - 1])
                throw new ArgumentException("each capture must start after the one before");
        if (starts[^1] > samples.Length)
            throw new ArgumentException($"a capture starts past the last of {samples.Length} samples");
        var result = new List<Signal<T>>(starts.Count);
        for (int j = 0; j < starts.Count; j++)
        {
            long a = starts[j];
            long b = j + 1 < starts.Count ? starts[j + 1] : samples.Length;
            bool last = j == starts.Count - 1;
            var md = (Dictionary<string, object?>)Copy(metadata)!;
            md.Remove(AnnotationsKey);
            var mine = new List<object?>();
            foreach (var x in annotations.Cast<Dictionary<string, object?>>())
            {
                long at = Convert.ToInt64(x["core:sample_start"], CultureInfo.InvariantCulture);
                if (a <= at && (last || at < b))
                {
                    var y = (Dictionary<string, object?>)Copy(x)!;
                    y["core:sample_start"] = at - a;
                    mine.Add(y);
                }
            }
            if (mine.Count > 0)
                md[AnnotationsKey] = mine;
            result.Add(make((samples[(int)a..(int)b], a, freqs[j], md)));
        }
        return result;
    }

    /// <summary>A deep copy of a JSON value, so channels read from one recording share no lists or objects.</summary>
    private static object? Copy(object? v) => v switch
    {
        List<object?> l => l.Select(Copy).ToList(),
        Dictionary<string, object?> d => d.ToDictionary(kv => kv.Key, kv => Copy(kv.Value)),
        _ => v,
    };

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
    /// <param name="info">Text tags, as for the multi-channel overload.</param>
    /// <param name="cues">Cue points, as for the multi-channel overload.</param>
    public static void WriteWav(string path, Signal<double> signal, string sampleFormat = "f32",
        IEnumerable<KeyValuePair<string, string>>? info = null, IReadOnlyList<(long Position, long Length, string Label)>? cues = null)
    {
        ArgumentNullException.ThrowIfNull(signal);
        WriteWav(path, [signal], sampleFormat, info, cues);
    }

    /// <summary>Writes real signals, one per channel, as a PCM or IEEE float WAV file (conventions: Signal files, WAV).
    /// Only the samples, the sample rate and the text tags are stored.</summary>
    /// <param name="path">The file to write.</param>
    /// <param name="channels">One or more signals with the same length and the same whole-number sample rate.</param>
    /// <param name="sampleFormat"><c>u8</c>, <c>i16</c>, <c>i24</c>, <c>i32</c> (PCM), <c>f32</c> or <c>f64</c> (IEEE float).</param>
    /// <param name="info">Text tags in order, written as a <c>LIST</c>/<c>INFO</c> chunk after the data: IDs of four
    /// characters from A-Z and 0-9, each once, to printable ASCII text (ADR 0091). None or empty writes no chunk.</param>
    /// <param name="cues">Cue points in order, written as a <c>cue </c> chunk after the data, with a <c>LIST</c>/<c>adtl</c>
    /// chunk for the non-empty labels and non-zero lengths: each a position in frames, a length in frames (0 for a point;
    /// position + length at most the signal length) and a printable ASCII label (ADR 0094, 0095). None or empty writes
    /// no chunk.</param>
    public static void WriteWav(string path, IReadOnlyList<Signal<double>> channels, string sampleFormat = "f32",
        IEnumerable<KeyValuePair<string, string>>? info = null, IReadOnlyList<(long Position, long Length, string Label)>? cues = null)
    {
        ArgumentException.ThrowIfNullOrEmpty(path);
        byte[] tags = WavInfoChunk(info);
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
        tags = [.. WavCueChunks(cues, n), .. tags];
        long nbytes = n * block;
        long riffSize = 4 + (isFloat ? 38 : 24) + 8 + nbytes + nbytes % 2 + tags.Length;
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
            bw.Write(tags);
        }
        File.WriteAllBytes(path, ms.ToArray());
    }

    /// <summary>The <c>cue </c> chunk and <c>LIST</c>/<c>adtl</c> labels and regions for <paramref name="cues"/>, or
    /// nothing when it is empty.</summary>
    private static byte[] WavCueChunks(IReadOnlyList<(long Position, long Length, string Label)>? cues, int frames)
    {
        if (cues is null || cues.Count == 0)
            return [];
        var points = new MemoryStream();
        var labels = new MemoryStream();
        Span<byte> point = stackalloc byte[24];
        for (int i = 0; i < cues.Count; i++)
        {
            (long pos, long length, string label) = cues[i];
            uint id = (uint)(i + 1);
            if (pos < 0 || pos > frames)
                throw new ArgumentException($"cue position {pos} must be a whole number from 0 to {frames}", nameof(cues));
            if (length < 0 || length > frames - pos)
                throw new ArgumentException($"cue length {length} must be a whole number from 0 to {frames - pos}", nameof(cues));
            if (label is null || label.Any(c => c is < ' ' or > '~'))
                throw new ArgumentException($"cue label '{label}' must be printable ASCII text", nameof(cues));
            BinaryPrimitives.WriteUInt32LittleEndian(point, id);
            BinaryPrimitives.WriteUInt32LittleEndian(point[4..], (uint)pos);
            "data"u8.CopyTo(point[8..]);
            BinaryPrimitives.WriteUInt32LittleEndian(point[12..], 0);
            BinaryPrimitives.WriteUInt32LittleEndian(point[16..], 0);
            BinaryPrimitives.WriteUInt32LittleEndian(point[20..], (uint)pos);
            points.Write(point);
            if (label.Length > 0)
            {
                byte[] body = new byte[4 + label.Length + 1];
                BinaryPrimitives.WriteUInt32LittleEndian(body, id);
                System.Text.Encoding.ASCII.GetBytes(label).CopyTo(body, 4);
                labels.Write(RiffChunk("labl"u8, body));
            }
            if (length > 0)
            {
                byte[] body = new byte[20]; // ID, length, purpose; country, language, dialect, code page 0
                BinaryPrimitives.WriteUInt32LittleEndian(body, id);
                BinaryPrimitives.WriteUInt32LittleEndian(body.AsSpan(4), (uint)length);
                "rgn "u8.CopyTo(body.AsSpan(8));
                labels.Write(RiffChunk("ltxt"u8, body));
            }
        }
        byte[] count = new byte[4];
        BinaryPrimitives.WriteUInt32LittleEndian(count, (uint)cues.Count);
        byte[] cue = RiffChunk("cue "u8, [.. count, .. points.ToArray()]);
        return labels.Length == 0 ? cue : [.. cue, .. RiffChunk("LIST"u8, [.. "adtl"u8, .. labels.ToArray()])];
    }

    /// <summary>A RIFF chunk: the ID, the 32-bit size, the body and a zero pad byte when the size is odd.</summary>
    private static byte[] RiffChunk(ReadOnlySpan<byte> id, byte[] body)
    {
        byte[] chunk = new byte[8 + body.Length + body.Length % 2];
        id.CopyTo(chunk);
        BinaryPrimitives.WriteUInt32LittleEndian(chunk.AsSpan(4), (uint)body.Length);
        body.CopyTo(chunk, 8);
        return chunk;
    }

    /// <summary>The <c>LIST</c>/<c>INFO</c> chunk for <paramref name="info"/>, or nothing when it is empty.</summary>
    private static byte[] WavInfoChunk(IEnumerable<KeyValuePair<string, string>>? info)
    {
        if (info is null)
            return [];
        var subs = new MemoryStream();
        var seen = new HashSet<string>(StringComparer.Ordinal);
        Span<byte> size = stackalloc byte[4];
        foreach ((string id, string text) in info)
        {
            if (id is not { Length: 4 } || id.Any(c => c is not ((>= 'A' and <= 'Z') or (>= '0' and <= '9'))))
                throw new ArgumentException($"info ID '{id}' must be four characters from A-Z and 0-9", nameof(info));
            if (!seen.Add(id))
                throw new ArgumentException($"info ID '{id}' is used twice", nameof(info));
            if (text is null || text.Any(c => c is < ' ' or > '~'))
                throw new ArgumentException($"info['{id}'] must be printable ASCII text", nameof(info));
            subs.Write(System.Text.Encoding.ASCII.GetBytes(id));
            BinaryPrimitives.WriteUInt32LittleEndian(size, (uint)(text.Length + 1));
            subs.Write(size);
            subs.Write(System.Text.Encoding.ASCII.GetBytes(text));
            subs.WriteByte(0);
            if (text.Length % 2 == 0) // the body (text + NUL) is odd: pad it
                subs.WriteByte(0);
        }
        if (subs.Length == 0)
            return [];
        byte[] chunk = new byte[12 + subs.Length];
        "LIST"u8.CopyTo(chunk);
        BinaryPrimitives.WriteUInt32LittleEndian(chunk.AsSpan(4), (uint)(4 + subs.Length));
        "INFO"u8.CopyTo(chunk.AsSpan(8));
        subs.ToArray().CopyTo(chunk, 12);
        return chunk;
    }

    /// <summary>Reads the text tags of every <c>LIST</c>/<c>INFO</c> chunk in a WAV file, in file order, IDs and texts
    /// decoded byte for byte as Latin-1 (conventions: Signal files, WAV; ADR 0091).</summary>
    /// <param name="path">The file to read.</param>
    /// <returns>Each ID and its text.</returns>
    /// <exception cref="ArgumentException">The file is not a RIFF WAVE file, a chunk runs past its end, or an ID
    /// appears twice.</exception>
    public static OrderedDictionary<string, string> ReadWavInfo(string path)
    {
        ArgumentException.ThrowIfNullOrEmpty(path);
        byte[] raw = File.ReadAllBytes(path);
        if (raw.Length < 12 || !raw.AsSpan(0, 4).SequenceEqual("RIFF"u8) || !raw.AsSpan(8, 4).SequenceEqual("WAVE"u8))
            throw new ArgumentException("not a RIFF WAVE file", nameof(path));
        var result = new OrderedDictionary<string, string>(StringComparer.Ordinal);
        foreach ((string id, int start, int end) in RiffWalk(raw, 12, raw.Length, "chunk", nameof(path)))
        {
            if (id != "LIST" || end - start < 4 || !raw.AsSpan(start, 4).SequenceEqual("INFO"u8))
                continue;
            foreach ((string key, int s, int e) in RiffWalk(raw, start + 4, end, "INFO subchunk", nameof(path)))
            {
                ReadOnlySpan<byte> body = raw.AsSpan(s, e - s);
                int nul = body.IndexOf((byte)0);
                if (!result.TryAdd(key, System.Text.Encoding.Latin1.GetString(nul < 0 ? body : body[..nul])))
                    throw new ArgumentException($"the info ID '{key}' appears twice", nameof(path));
            }
        }
        return result;
    }

    /// <summary>Reads the cue points of a WAV file's <c>cue </c> chunk, in its order, with their labels from
    /// <c>LIST</c>/<c>adtl</c> <c>labl</c> subchunks and their lengths from <c>ltxt</c> subchunks (conventions: Signal
    /// files, WAV; ADR 0094, 0095).</summary>
    /// <param name="path">The file to read.</param>
    /// <returns>Each point's position in frames from the start of the data, its length in frames (0 for none) and its
    /// label (empty for none).</returns>
    /// <exception cref="ArgumentException">The file is not a RIFF WAVE file with <c>fmt </c> and <c>data</c> chunks, or
    /// its cue points, labels or regions break the rules of ADR 0094 and 0095.</exception>
    public static IReadOnlyList<(long Position, long Length, string Label)> ReadWavCues(string path)
    {
        ArgumentException.ThrowIfNullOrEmpty(path);
        byte[] raw = File.ReadAllBytes(path);
        ArgumentException Bad(string message) => new(message, nameof(path));
        uint U32(int i) => BinaryPrimitives.ReadUInt32LittleEndian(raw.AsSpan(i));
        if (raw.Length < 12 || !raw.AsSpan(0, 4).SequenceEqual("RIFF"u8) || !raw.AsSpan(8, 4).SequenceEqual("WAVE"u8))
            throw Bad("not a RIFF WAVE file");
        int? block = null;
        long? dataBytes = null;
        OrderedDictionary<uint, long>? points = null;
        var labels = new Dictionary<uint, string>();
        var lengths = new Dictionary<uint, long>();
        foreach ((string id, int start, int end) in RiffWalk(raw, 12, raw.Length, "chunk", nameof(path)))
        {
            if (id == "fmt " && block is null)
            {
                if (end - start < 16)
                    throw Bad("the fmt chunk is shorter than 16 bytes");
                block = BinaryPrimitives.ReadUInt16LittleEndian(raw.AsSpan(start + 12));
            }
            else if (id == "data" && dataBytes is null)
            {
                dataBytes = end - start;
            }
            else if (id == "cue ")
            {
                if (points is not null)
                    throw Bad("there are two cue chunks");
                points = [];
                if (end - start < 4)
                    throw Bad("the cue chunk is shorter than 4 bytes");
                long count = U32(start);
                if (end - start != 4 + 24 * count)
                    throw Bad($"the cue chunk is not 4 + 24 x {count} bytes");
                for (int k = 0; k < count; k++)
                {
                    int at = start + 4 + 24 * k;
                    uint cueId = U32(at);
                    if (!raw.AsSpan(at + 8, 4).SequenceEqual("data"u8) || U32(at + 12) != 0 || U32(at + 16) != 0)
                        throw Bad($"cue {cueId} does not point straight into the data chunk");
                    if (!points.TryAdd(cueId, U32(at + 20)))
                        throw Bad($"the cue ID {cueId} appears twice");
                }
            }
            else if (id == "LIST" && end - start >= 4 && raw.AsSpan(start, 4).SequenceEqual("adtl"u8))
            {
                foreach ((string sid, int s, int e) in RiffWalk(raw, start + 4, end, "adtl subchunk", nameof(path)))
                {
                    if (sid == "ltxt")
                    {
                        if (e - s < 20)
                            throw Bad("an ltxt subchunk is shorter than 20 bytes");
                        if (!lengths.TryAdd(U32(s), U32(s + 4)))
                            throw Bad($"cue {U32(s)} has two ltxt subchunks");
                        continue;
                    }
                    if (sid != "labl")
                        continue;
                    if (e - s < 4)
                        throw Bad("a labl subchunk is shorter than 4 bytes");
                    uint cueId = U32(s);
                    ReadOnlySpan<byte> text = raw.AsSpan(s + 4, e - s - 4);
                    int nul = text.IndexOf((byte)0);
                    if (!labels.TryAdd(cueId, System.Text.Encoding.Latin1.GetString(nul < 0 ? text : text[..nul])))
                        throw Bad($"cue {cueId} has two labels");
                }
            }
        }
        if (block is null)
            throw Bad("no fmt chunk");
        if (dataBytes is null)
            throw Bad("no data chunk");
        if (block == 0)
            throw Bad("the block align is 0");
        points ??= [];
        if (labels.Keys.Any(k => !points.ContainsKey(k)))
            throw Bad("a label names a cue ID with no cue point");
        if (lengths.Keys.Any(k => !points.ContainsKey(k)))
            throw Bad("an ltxt names a cue ID with no cue point");
        long frames = dataBytes.Value / block.Value;
        if (points.Values.Any(p => p > frames))
            throw Bad($"a cue point is past the last of {frames} frames");
        if (lengths.Any(kv => points[kv.Key] + kv.Value > frames))
            throw Bad($"a cue region runs past the last of {frames} frames");
        return [.. points.Select(kv => (kv.Value, lengths.GetValueOrDefault(kv.Key), labels.GetValueOrDefault(kv.Key, "")))];
    }

    /// <summary>(id, body start, body end) of each chunk from <paramref name="pos"/> until fewer than 8 bytes are left.</summary>
    private static List<(string Id, int Start, int End)> RiffWalk(byte[] raw, int pos, int stop, string what, string param)
    {
        var chunks = new List<(string, int, int)>();
        while ((long)pos + 8 <= stop)
        {
            string id = System.Text.Encoding.Latin1.GetString(raw, pos, 4);
            long size = BinaryPrimitives.ReadUInt32LittleEndian(raw.AsSpan(pos + 4));
            if (pos + 8 + size > stop)
                throw new ArgumentException($"the '{id}' {what} runs past its end", param);
            chunks.Add((id, pos + 8, (int)(pos + 8 + size)));
            long next = pos + 8 + size + (size % 2);
            if (next >= stop)
                break;
            pos = (int)next;
        }
        return chunks;
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

    /// <summary>Writes a real 2-D array as a NumPy <c>.npy</c> file of <c>'&lt;f8'</c> in C order, in the layout
    /// <c>numpy.save</c> writes (conventions: Signal files, NumPy .npy; ADR 0092).</summary>
    /// <param name="path">The file to write.</param>
    /// <param name="x">The values, row by row; NaN and infinities included.</param>
    public static void WriteNpy(string path, double[,] x)
    {
        ArgumentException.ThrowIfNullOrEmpty(path);
        ArgumentNullException.ThrowIfNull(x);
        File.WriteAllBytes(path, NpyBytes("<f8", Shape2D(x), Bytes2D(x, 8)));
    }

    /// <summary>Writes a complex 2-D array as a NumPy <c>.npy</c> file of <c>'&lt;c16'</c> in C order, in the layout
    /// <c>numpy.save</c> writes (conventions: Signal files, NumPy .npy; ADR 0092).</summary>
    /// <param name="path">The file to write.</param>
    /// <param name="x">The values, row by row, real then imaginary part of each.</param>
    public static void WriteNpy(string path, Complex[,] x)
    {
        ArgumentException.ThrowIfNullOrEmpty(path);
        ArgumentNullException.ThrowIfNull(x);
        File.WriteAllBytes(path, NpyBytes("<c16", Shape2D(x), Bytes2D(x, 16)));
    }

    private static string Shape2D(Array x) =>
        string.Create(CultureInfo.InvariantCulture, $"({x.GetLength(0)}, {x.GetLength(1)})");

    /// <summary>The bytes of a rectangular array, which .NET stores row by row (C order).</summary>
    private static ReadOnlySpan<byte> Bytes2D(Array x, int itemSize) =>
        MemoryMarshal.CreateReadOnlySpan(ref MemoryMarshal.GetArrayDataReference(x), checked(x.Length * itemSize));

    private static void WriteNpyFile(string path, string descr, int n, ReadOnlySpan<byte> native) =>
        File.WriteAllBytes(path, NpyBytes(descr, n, native));

    private static byte[] NpyBytes(string descr, int n, ReadOnlySpan<byte> native) =>
        NpyBytes(descr, string.Create(CultureInfo.InvariantCulture, $"({n},)"), native);

    private static byte[] NpyBytes(string descr, string shape, ReadOnlySpan<byte> native)
    {
        string text = $"{{'descr': '{descr}', 'fortran_order': False, 'shape': {shape}, }}";
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
        return file;
    }

    /// <summary>Reads a 1-D NumPy <c>.npy</c> file, versions 1.0 to 3.0, of binary64, binary32 or binary16
    /// floats or complex pairs in either byte order, widened exactly (conventions: Signal files, NumPy .npy;
    /// ADR 0088), or of 8- to 64-bit integers, read as doubles without scaling (ADR 0090). The header is
    /// parsed, never evaluated.</summary>
    /// <typeparam name="T"><see cref="double"/> for <c>f8</c>, <c>f4</c>, <c>f2</c> and the integers; <see cref="Complex"/> for
    /// <c>c16</c>, <c>c8</c>.</typeparam>
    /// <param name="path">The file to read.</param>
    /// <returns>The values.</returns>
    /// <exception cref="ArgumentException">The file is not a <c>.npy</c> file of <typeparamref name="T"/> this reads.</exception>
    public static T[] ReadNpy<T>(string path) where T : struct
    {
        ArgumentException.ThrowIfNullOrEmpty(path);
        bool wantComplex = typeof(T) == typeof(Complex);
        if (!wantComplex && typeof(T) != typeof(double))
            throw new ArgumentException($"the element type must be double or Complex, not {typeof(T).Name}", nameof(T));
        Array values = ParseNpy(File.ReadAllBytes(path), message => new ArgumentException(message, nameof(path)));
        return values as T[] ?? throw new ArgumentException(
            $"the file holds {(values is Complex[]? "complex" : "real")} values, not {typeof(T).Name}", nameof(path));
    }

    /// <summary>Reads a 2-D NumPy <c>.npy</c> file of shape <c>(rows, columns)</c>, in either <c>fortran_order</c>, with
    /// the dtypes <see cref="ReadNpy{T}(string)"/> reads (conventions: Signal files, NumPy .npy; ADR 0092).</summary>
    /// <typeparam name="T"><see cref="double"/> or <see cref="Complex"/>, as for <see cref="ReadNpy{T}(string)"/>.</typeparam>
    /// <param name="path">The file to read.</param>
    /// <returns>The values, indexed [row, column].</returns>
    /// <exception cref="ArgumentException">The file is not a 2-D <c>.npy</c> file of <typeparamref name="T"/> this reads.</exception>
    public static T[,] ReadNpy2D<T>(string path) where T : struct
    {
        ArgumentException.ThrowIfNullOrEmpty(path);
        bool wantComplex = typeof(T) == typeof(Complex);
        if (!wantComplex && typeof(T) != typeof(double))
            throw new ArgumentException($"the element type must be double or Complex, not {typeof(T).Name}", nameof(T));
        Array values = ParseNpy(File.ReadAllBytes(path), message => new ArgumentException(message, nameof(path)), 2,
            out long[] shape, out bool fortran);
        T[] flat = values as T[] ?? throw new ArgumentException(
            $"the file holds {(values is Complex[]? "complex" : "real")} values, not {typeof(T).Name}", nameof(path));
        return Reshape(flat, shape, fortran);
    }

    /// <summary>A 2-D array from its items in file order, C or Fortran (ADR 0092).</summary>
    private static T[,] Reshape<T>(T[] flat, long[] shape, bool fortran)
    {
        int rows = (int)shape[0], columns = (int)shape[1];
        var result = new T[rows, columns];
        for (int k = 0; k < flat.Length; k++)
        {
            if (fortran)
                result[k % rows, k / rows] = flat[k];
            else
                result[k / columns, k % columns] = flat[k];
        }
        return result;
    }

    /// <summary>A <c>.npz</c> member's values: 1-D as <see cref="ReadNpy{T}(string)"/> reads them, 2-D as
    /// <see cref="ReadNpy2D{T}(string)"/> does (ADR 0093).</summary>
    private static Array ParseNpzMember(byte[] raw, Func<string, ArgumentException> bad)
    {
        Array values = ParseNpy(raw, bad, 0, out long[] shape, out bool fortran);
        if (shape.Length == 1)
            return values;
        return values is Complex[] z ? Reshape(z, shape, fortran) : Reshape((double[])values, shape, fortran);
    }

    /// <summary>The largest 2-D dimension read: <see cref="Array.MaxLength"/>, written out so it cannot drift from the
    /// Python limit (ADR 0092).</summary>
    private const long NpyMaxDimension = 2147483591;

    /// <summary>The values in a 1-D <c>.npy</c> file's bytes: a <see cref="double"/>[] or a <see cref="Complex"/>[]
    /// (conventions: Signal files, NumPy .npy).</summary>
    private static Array ParseNpy(byte[] raw, Func<string, ArgumentException> bad) => ParseNpy(raw, bad, 1, out _, out _);

    /// <summary>The values in a <c>.npy</c> file's bytes in file order, for a shape of <paramref name="ndim"/> integers, or
    /// of 1 or 2 when <paramref name="ndim"/> is 0.</summary>
    private static Array ParseNpy(byte[] raw, Func<string, ArgumentException> bad, int ndim, out long[] shape, out bool fortran)
    {
        if (raw.Length < 8 || !raw.AsSpan(0, 6).SequenceEqual(NpyMagic))
            throw bad("not a .npy file");
        int width = (raw[6], raw[7]) switch
        {
            (1, 0) => 2,
            (2, 0) or (3, 0) => 4,
            _ => throw bad($".npy version {raw[6]}.{raw[7]} is not supported"),
        };
        if (raw.Length < 8 + width)
            throw bad("the .npy file ends inside its header length");
        long size = width == 2 ? BinaryPrimitives.ReadUInt16LittleEndian(raw.AsSpan(8)) : BinaryPrimitives.ReadUInt32LittleEndian(raw.AsSpan(8));
        long start = 8 + width + size;
        if (start > raw.Length)
            throw bad("the .npy header runs past the end of the file");
        ReadOnlySpan<byte> head = raw.AsSpan(8 + width, (int)size);
        if (head.ContainsAnyInRange((byte)128, (byte)255))
            throw bad("the .npy header must be ASCII");
        Dictionary<string, object> d = new NpyHeader(System.Text.Encoding.ASCII.GetString(head), bad).Parse();
        if (d.Count != 3 || !d.TryGetValue("descr", out object? descr) || !d.TryGetValue("fortran_order", out object? order)
            || !d.TryGetValue("shape", out object? shapeValue))
            throw bad("the .npy header needs exactly descr, fortran_order and shape");
        // Floats, complex and integers (ADR 0088, ADR 0090); a one-byte integer has the byte order '|'.
        if (descr is not string { Length: >= 3 } ds
            || !(ds is "|i1" or "|u1" || (ds[0] is '<' or '>'
                && ds[1..] is "f8" or "f4" or "f2" or "c16" or "c8" or "i2" or "u2" or "i4" or "u4" or "i8" or "u8")))
            throw bad($"descr {descr} is not one ReadNpy reads");
        if (order is not bool isFortran)
            throw bad("fortran_order must be True or False");
        if (shapeValue is not long[] shp || (ndim == 0 ? shp.Length is not (1 or 2) : shp.Length != ndim))
            throw bad(ndim == 0 ? "only 1-D and 2-D arrays are read here"
                : string.Create(CultureInfo.InvariantCulture, $"only {ndim}-D arrays are read here"));
        if (shp.Length == 2 && shp.Max() > NpyMaxDimension)
            throw bad("the shape has a dimension beyond 2147483591");
        (shape, fortran) = (shp, isFortran);
        long count = shp.Aggregate(1L, (p, n) => p * n); // no overflow: two dimensions are below 2^31
        char kind = ds[1];
        bool isComplex = kind == 'c', little = ds[0] != '>';
        int partSize = int.Parse(ds.AsSpan(2), CultureInfo.InvariantCulture) / (isComplex ? 2 : 1); // bytes per part
        int parts = isComplex ? 2 : 1;
        long bytes = raw.Length - start;
        if (bytes % (partSize * parts) != 0 || bytes / (partSize * parts) != count)
            throw bad(string.Create(CultureInfo.InvariantCulture,
                $"{bytes} data bytes do not match shape ({string.Join(", ", shp)}{(ndim == 1 ? "," : "")})"));
        var values = new double[bytes / partSize];
        ReadOnlySpan<byte> src = raw.AsSpan((int)start);
        for (int i = 0; i < values.Length; i++)
        {
            ReadOnlySpan<byte> b = src.Slice(i * partSize, partSize);
            values[i] = (kind, partSize, little) switch
            {
                ('f' or 'c', 8, true) => BinaryPrimitives.ReadDoubleLittleEndian(b),
                ('f' or 'c', 8, false) => BinaryPrimitives.ReadDoubleBigEndian(b),
                ('f' or 'c', 4, true) => BinaryPrimitives.ReadSingleLittleEndian(b),
                ('f' or 'c', 4, false) => BinaryPrimitives.ReadSingleBigEndian(b),
                ('f' or 'c', _, true) => (double)BinaryPrimitives.ReadHalfLittleEndian(b),
                ('f' or 'c', _, false) => (double)BinaryPrimitives.ReadHalfBigEndian(b),
                ('i', 1, _) => (sbyte)b[0],
                ('u', 1, _) => b[0],
                ('i', 2, true) => BinaryPrimitives.ReadInt16LittleEndian(b),
                ('i', 2, false) => BinaryPrimitives.ReadInt16BigEndian(b),
                ('u', 2, true) => BinaryPrimitives.ReadUInt16LittleEndian(b),
                ('u', 2, false) => BinaryPrimitives.ReadUInt16BigEndian(b),
                ('i', 4, true) => BinaryPrimitives.ReadInt32LittleEndian(b),
                ('i', 4, false) => BinaryPrimitives.ReadInt32BigEndian(b),
                ('u', 4, true) => BinaryPrimitives.ReadUInt32LittleEndian(b),
                ('u', 4, false) => BinaryPrimitives.ReadUInt32BigEndian(b),
                // (double) of a 64-bit integer rounds to nearest, ties to even (ADR 0090).
                ('i', _, true) => BinaryPrimitives.ReadInt64LittleEndian(b),
                ('i', _, false) => BinaryPrimitives.ReadInt64BigEndian(b),
                (_, _, true) => BinaryPrimitives.ReadUInt64LittleEndian(b),
                _ => BinaryPrimitives.ReadUInt64BigEndian(b),
            };
        }
        if (!isComplex)
            return values;
        var z = new Complex[values.Length / 2];
        for (int i = 0; i < z.Length; i++)
            z[i] = new Complex(values[2 * i], values[(2 * i) + 1]);
        return z;
    }

    private static readonly uint[] Crc32Table = [.. Enumerable.Range(0, 256).Select(n =>
    {
        uint c = (uint)n;
        for (int k = 0; k < 8; k++)
            c = (c & 1) != 0 ? 0xEDB88320 ^ (c >> 1) : c >> 1;
        return c;
    })];

    /// <summary>The ZIP CRC-32 (reflected polynomial 0xEDB88320).</summary>
    private static uint Crc32(ReadOnlySpan<byte> data)
    {
        uint c = 0xFFFFFFFF;
        foreach (byte b in data)
            c = Crc32Table[(c ^ b) & 0xFF] ^ (c >> 8);
        return ~c;
    }

    /// <summary>Writes 1-D or 2-D arrays as a NumPy <c>.npz</c> archive: one uncompressed <c>&lt;key&gt;.npy</c>
    /// member each, in order (conventions: Signal files, NumPy .npz; ADRs 0089 and 0093).</summary>
    /// <param name="path">The file to write.</param>
    /// <param name="arrays">Names (1 to 250 printable ASCII characters, no <c>/</c> or <c>\</c>, each once)
    /// and their values, each a <see cref="double"/>[], <see cref="Complex"/>[], <see cref="double"/>[,] or
    /// <see cref="Complex"/>[,]; a 2-D value is written in C order.</param>
    public static void WriteNpz(string path, IEnumerable<KeyValuePair<string, Array>> arrays)
    {
        ArgumentException.ThrowIfNullOrEmpty(path);
        ArgumentNullException.ThrowIfNull(arrays);
        var body = new MemoryStream();
        var central = new MemoryStream();
        var seen = new HashSet<string>(StringComparer.Ordinal);
        Span<byte> h = stackalloc byte[46];
        foreach ((string key, Array x) in arrays)
        {
            if (key is null || key.Length is < 1 or > 250 || key.Any(c => c is < ' ' or > '~' or '/' or '\\'))
                throw new ArgumentException($"name '{key}' must be 1 to 250 printable ASCII characters, no / or \\", nameof(arrays));
            if (!seen.Add(key))
                throw new ArgumentException($"name '{key}' is used twice", nameof(arrays));
            if (seen.Count > 65535)
                throw new ArgumentException("an archive holds at most 65535 arrays", nameof(arrays));
            byte[] data = x switch
            {
                double[] r => NpyBytes("<f8", r.Length, MemoryMarshal.AsBytes(r.AsSpan())),
                Complex[] z => NpyBytes("<c16", z.Length, MemoryMarshal.AsBytes(z.AsSpan())),
                double[,] r2 => NpyBytes("<f8", Shape2D(r2), Bytes2D(r2, 8)),
                Complex[,] z2 => NpyBytes("<c16", Shape2D(z2), Bytes2D(z2, 16)),
                _ => throw new ArgumentException(
                    $"arrays['{key}'] must be a double[], Complex[], double[,] or Complex[,]", nameof(arrays)),
            };
            byte[] name = System.Text.Encoding.ASCII.GetBytes(key + ".npy");
            uint crc = Crc32(data), offset = (uint)body.Length;
            h.Clear();
            BinaryPrimitives.WriteUInt32LittleEndian(h, 0x04034B50);
            BinaryPrimitives.WriteUInt16LittleEndian(h[4..], 20);
            BinaryPrimitives.WriteUInt16LittleEndian(h[12..], 0x0021);
            BinaryPrimitives.WriteUInt32LittleEndian(h[14..], crc);
            BinaryPrimitives.WriteUInt32LittleEndian(h[18..], (uint)data.Length);
            BinaryPrimitives.WriteUInt32LittleEndian(h[22..], (uint)data.Length);
            BinaryPrimitives.WriteUInt16LittleEndian(h[26..], (ushort)name.Length);
            body.Write(h[..30]);
            body.Write(name);
            body.Write(data);
            h.Clear();
            BinaryPrimitives.WriteUInt32LittleEndian(h, 0x02014B50);
            BinaryPrimitives.WriteUInt16LittleEndian(h[4..], 20);
            BinaryPrimitives.WriteUInt16LittleEndian(h[6..], 20);
            BinaryPrimitives.WriteUInt16LittleEndian(h[14..], 0x0021);
            BinaryPrimitives.WriteUInt32LittleEndian(h[16..], crc);
            BinaryPrimitives.WriteUInt32LittleEndian(h[20..], (uint)data.Length);
            BinaryPrimitives.WriteUInt32LittleEndian(h[24..], (uint)data.Length);
            BinaryPrimitives.WriteUInt16LittleEndian(h[28..], (ushort)name.Length);
            BinaryPrimitives.WriteUInt32LittleEndian(h[42..], offset);
            central.Write(h);
            central.Write(name);
            if (body.Length + central.Length + 22 >= 1L << 32)
                throw new ArgumentException("the archive would reach 4 GiB, which needs ZIP64", nameof(arrays));
        }
        Span<byte> end = stackalloc byte[22];
        end.Clear();
        BinaryPrimitives.WriteUInt32LittleEndian(end, 0x06054B50);
        BinaryPrimitives.WriteUInt16LittleEndian(end[8..], (ushort)seen.Count);
        BinaryPrimitives.WriteUInt16LittleEndian(end[10..], (ushort)seen.Count);
        BinaryPrimitives.WriteUInt32LittleEndian(end[12..], (uint)central.Length);
        BinaryPrimitives.WriteUInt32LittleEndian(end[16..], (uint)body.Length);
        using var file = File.Create(path);
        body.WriteTo(file);
        central.WriteTo(file);
        file.Write(end);
    }

    /// <summary>Reads a NumPy <c>.npz</c> archive of stored or deflated <c>.npy</c> members, in member order. The
    /// ZIP is parsed here, not by <c>ZipArchive</c> (conventions: Signal files, NumPy .npz; ADR 0089).</summary>
    /// <param name="path">The file to read.</param>
    /// <returns>Each key and its values: a <see cref="double"/>[] or <see cref="Complex"/>[] for a 1-D member, a
    /// <see cref="double"/>[,] or <see cref="Complex"/>[,] for a 2-D one (ADR 0093).</returns>
    /// <exception cref="ArgumentException">The file is not a <c>.npz</c> archive this reads.</exception>
    public static OrderedDictionary<string, Array> ReadNpz(string path)
    {
        ArgumentException.ThrowIfNullOrEmpty(path);
        byte[] raw = File.ReadAllBytes(path);
        ArgumentException Bad(string message) => new(message, nameof(path));
        ushort U16(long i) => BinaryPrimitives.ReadUInt16LittleEndian(raw.AsSpan((int)i));
        uint U32(long i) => BinaryPrimitives.ReadUInt32LittleEndian(raw.AsSpan((int)i));
        long at = -1;
        for (long i = raw.Length - 22; i >= Math.Max(0, raw.Length - 65557); i--)
        {
            if (U32(i) == 0x06054B50 && i + 22 + U16(i + 20) == raw.Length)
            {
                at = i;
                break;
            }
        }
        if (at < 0)
            throw Bad("not a ZIP archive: no end record");
        if (U16(at + 4) != 0 || U16(at + 6) != 0)
            throw Bad("multi-disk archives are not read");
        int count = U16(at + 10);
        if (U16(at + 8) != count)
            throw Bad("the end record's two member counts differ");
        long cdSize = U32(at + 12), cdAt = U32(at + 16);
        if (count == 0xFFFF || cdSize == 0xFFFFFFFF || cdAt == 0xFFFFFFFF)
            throw Bad("archives that need ZIP64 are not read");
        if (cdAt + cdSize > at)
            throw Bad("the central directory runs past the end record");
        var result = new OrderedDictionary<string, Array>(StringComparer.Ordinal);
        long p = cdAt, cdEnd = cdAt + cdSize;
        for (int m = 0; m < count; m++)
        {
            if (p + 46 > cdEnd || U32(p) != 0x02014B50)
                throw Bad("a central directory header is missing");
            int flags = U16(p + 8), method = U16(p + 10);
            uint crc = U32(p + 16);
            long csize = U32(p + 20), usize = U32(p + 24), offset = U32(p + 42);
            int nlen = U16(p + 28), xlen = U16(p + 30), clen = U16(p + 32);
            long nameEnd = p + 46 + nlen;
            if (nameEnd + xlen + clen > cdEnd)
                throw Bad("a central directory header runs past the directory");
            byte[] nameRaw = raw[(int)(p + 46)..(int)nameEnd];
            ReadOnlySpan<byte> extra = raw.AsSpan((int)nameEnd, xlen);
            p = nameEnd + xlen + clen;
            if ((flags & 1) != 0)
                throw Bad("encrypted members are not read");
            if (method is not (0 or 8))
                throw Bad(string.Create(CultureInfo.InvariantCulture, $"compression method {method} is not read (only stored and deflate)"));
            (usize, csize, offset) = Zip64Fields(extra, usize, csize, offset, Bad);
            string name;
            try
            {
                name = (flags & 0x800) != 0
                    ? new System.Text.UTF8Encoding(false, true).GetString(nameRaw)
                    : nameRaw.Any(b => b > 127) ? throw Bad("a member name is not valid text") : System.Text.Encoding.ASCII.GetString(nameRaw);
            }
            catch (System.Text.DecoderFallbackException)
            {
                throw Bad("a member name is not valid text");
            }
            if (!name.EndsWith(".npy", StringComparison.Ordinal) || name.Length == 4)
                throw Bad($"member '{name}' is not a .npy array");
            string key = name[..^4];
            if (result.ContainsKey(key))
                throw Bad($"the archive has '{key}' twice");
            if (offset + 30 > raw.Length || U32(offset) != 0x04034B50)
                throw Bad($"member '{name}' has no local header");
            long start = offset + 30 + U16(offset + 26) + U16(offset + 28);
            if (start + csize > raw.Length)
                throw Bad($"member '{name}' runs past the end of the file");
            byte[] data;
            if (method == 0)
            {
                data = raw[(int)start..(int)(start + csize)];
            }
            else
            {
                if (usize > int.MaxValue - 1)
                    throw Bad($"member '{name}' is too large");
                using var inflate = new System.IO.Compression.DeflateStream(
                    new MemoryStream(raw, (int)start, (int)csize), System.IO.Compression.CompressionMode.Decompress);
                var buffer = new byte[usize + 1];
                int got = 0;
                try
                {
                    for (int r; got < buffer.Length && (r = inflate.Read(buffer, got, buffer.Length - got)) > 0;)
                        got += r;
                }
                catch (InvalidDataException)
                {
                    throw Bad($"member '{name}' is not valid deflate data");
                }
                data = buffer[..got];
            }
            if (data.Length != usize)
                throw Bad(string.Create(CultureInfo.InvariantCulture, $"member '{name}' is not {usize} bytes"));
            if (Crc32(data) != crc)
                throw Bad($"member '{name}' fails its CRC-32");
            result.Add(key, ParseNpzMember(data, Bad));
        }
        return result;
    }

    /// <summary>Sizes and offset, with each 0xFFFFFFFF taken from the ZIP64 extra field (0x0001).</summary>
    private static (long USize, long CSize, long Offset) Zip64Fields(ReadOnlySpan<byte> extra, long usize, long csize, long offset,
        Func<string, ArgumentException> bad)
    {
        bool[] need = [usize == 0xFFFFFFFF, csize == 0xFFFFFFFF, offset == 0xFFFFFFFF];
        if (!need.Any(v => v))
            return (usize, csize, offset);
        for (int j = 0; j + 4 <= extra.Length;)
        {
            int tag = BinaryPrimitives.ReadUInt16LittleEndian(extra[j..]), size = BinaryPrimitives.ReadUInt16LittleEndian(extra[(j + 2)..]);
            if (tag == 1)
            {
                int available = j + 4 + size <= extra.Length ? size / 8 : 0, next = 0;
                long[] got = [usize, csize, offset];
                for (int k = 0; k < 3; k++)
                {
                    if (!need[k])
                        continue;
                    if (next >= available)
                        throw bad("the ZIP64 extra field is too short");
                    ulong v = BinaryPrimitives.ReadUInt64LittleEndian(extra[(j + 4 + (8 * next++))..]);
                    got[k] = v > int.MaxValue ? throw bad("a ZIP64 size or offset is too large") : (long)v;
                }
                return (got[0], got[1], got[2]);
            }
            j += 4 + size;
        }
        throw bad("a ZIP64 size or offset has no ZIP64 extra field");
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
