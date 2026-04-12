namespace AI_M_OS.SystemMonitor.Services;

public record NetSnapshot(string Iface, long RxBytes, long TxBytes, DateTime Time);
public record DiskSnapshot(string Device, long SectorsRead, long SectorsWritten, DateTime Time);
public record IoRate(double ReadBytesPerSec, double WriteBytesPerSec);

public static class SystemMetrics
{
    private const string ProcNetDev    = "/proc/net/dev";
    private const string ProcDiskStats = "/proc/diskstats";
    private const int    SectorBytes   = 512;

    public static IReadOnlyList<NetSnapshot> ReadNetSnapshots()
    {
        var results = new List<NetSnapshot>();
        var now = DateTime.UtcNow;
        foreach (var line in File.ReadLines(ProcNetDev).Skip(2))
        {
            var c = line.IndexOf(':');
            if (c < 0) continue;
            var iface = line[..c].Trim();
            if (iface == "lo") continue;
            var p = line[(c + 1)..].Split(' ', StringSplitOptions.RemoveEmptyEntries);
            if (p.Length < 9) continue;
            if (!long.TryParse(p[0], out var rx)) continue;
            if (!long.TryParse(p[8], out var tx)) continue;
            results.Add(new NetSnapshot(iface, rx, tx, now));
        }
        return results;
    }

    public static IoRate? ComputeNetRate(NetSnapshot prev, NetSnapshot curr)
    {
        var e = (curr.Time - prev.Time).TotalSeconds;
        if (e <= 0) return null;
        return new IoRate((curr.RxBytes - prev.RxBytes) / e,
                          (curr.TxBytes - prev.TxBytes) / e);
    }

    public static IReadOnlyList<DiskSnapshot> ReadDiskSnapshots()
    {
        var results = new List<DiskSnapshot>();
        var now = DateTime.UtcNow;
        foreach (var line in File.ReadLines(ProcDiskStats))
        {
            var p = line.Split(' ', StringSplitOptions.RemoveEmptyEntries);
            if (p.Length < 10) continue;
            var dev = p[2];
            if (IsPartition(dev)) continue;
            if (!long.TryParse(p[5], out var sr)) continue;
            if (!long.TryParse(p[9], out var sw)) continue;
            results.Add(new DiskSnapshot(dev, sr, sw, now));
        }
        return results;
    }

    public static IoRate? ComputeDiskRate(DiskSnapshot prev, DiskSnapshot curr)
    {
        var e = (curr.Time - prev.Time).TotalSeconds;
        if (e <= 0) return null;
        return new IoRate(
            (curr.SectorsRead    - prev.SectorsRead)    * SectorBytes / e,
            (curr.SectorsWritten - prev.SectorsWritten) * SectorBytes / e);
    }

    private static bool IsPartition(string n)
    {
        if (n.Length == 0) return false;
        if (n.Contains("nvme") && n.Contains('p') && char.IsDigit(n[^1])) return true;
        if ((n.StartsWith("sd") || n.StartsWith("vd") || n.StartsWith("hd"))
            && char.IsDigit(n[^1])) return true;
        return false;
    }

    public static string FormatRate(double bps) => bps switch
    {
        >= 1_073_741_824 => $"{bps / 1_073_741_824.0:F1} GB/s",
        >= 1_048_576     => $"{bps / 1_048_576.0:F1} MB/s",
        >= 1_024         => $"{bps / 1_024.0:F1} KB/s",
        _                => $"{bps:F0} B/s"
    };

    // Нормализует значение в диапазон 0..1 для LevelBar
    public static double Normalize(double value, double max)
        => max <= 0 ? 0 : Math.Min(value / max, 1.0);
}
