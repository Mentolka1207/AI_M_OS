using Gtk;
using AI_M_OS.SystemMonitor.Services;

namespace AI_M_OS.SystemMonitor.Widgets;

public class DiskWidget : IDisposable
{
    private const uint PollMs = 1000;
    private record DevState(Label RdLabel, Label WrLabel,
                             LevelBar RdBar, LevelBar WrBar,
                             Queue<double> RH, Queue<double> WH);
    private readonly Dictionary<string, DevState> _devs = new();
    private readonly Box _container;
    private List<DiskSnapshot> _prev = [];
    private uint _timerId;
    private bool _disposed;

    public Widget Root => _container;

    public DiskWidget()
    {
        _container = Box.New(Orientation.Vertical, 8);
        var title = Label.New("o  DISK I/O");
        title.AddCssClass("section-title");
        title.Halign = Align.Start;
        _container.Append(title);
        _prev = [..SystemMetrics.ReadDiskSnapshots()];
        _timerId = GLib.Functions.TimeoutAdd(0, PollMs, Tick);
    }

    private bool Tick()
    {
        try
        {
            var curr = SystemMetrics.ReadDiskSnapshots();
            foreach (var s in curr)
            {
                var p = _prev.Find(x => x.Device == s.Device); if (p is null) continue;
                var r = SystemMetrics.ComputeDiskRate(p, s);    if (r is null) continue;
                if (!_devs.TryGetValue(s.Device, out var st))
                { st = MakeRow(s.Device); _devs[s.Device] = st; }
                Enqueue(st.RH, r.ReadBytesPerSec);
                Enqueue(st.WH, r.WriteBytesPerSec);
                st.RdLabel.SetText("R " + SystemMetrics.FormatRate(r.ReadBytesPerSec));
                st.WrLabel.SetText("W " + SystemMetrics.FormatRate(r.WriteBytesPerSec));
                st.RdBar.Value = SystemMetrics.Normalize(r.ReadBytesPerSec, st.RH.Max());
                st.WrBar.Value = SystemMetrics.Normalize(r.WriteBytesPerSec, st.WH.Max());
            }
            _prev = [..curr];
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine("[DiskWidget] Tick error: " + ex.Message);
        }
        return true;    }

    private DevState MakeRow(string dev)
    {
        var card = Box.New(Orientation.Vertical, 6);
        card.AddCssClass("glass-card");
        var name = Label.New("/dev/" + dev);
        name.AddCssClass("iface-name"); name.Halign = Align.Start;
        card.Append(name);
        var rdRow = Box.New(Orientation.Horizontal, 8);
        var rdLbl = Label.New("R 0 B/s"); rdLbl.AddCssClass("rate-rx");
        rdLbl.Halign = Align.Start; rdLbl.Hexpand = true;
        var rdBar = LevelBar.New(); rdBar.Hexpand = true;
        rdRow.Append(rdLbl); rdRow.Append(rdBar);
        card.Append(rdRow);        var wrRow = Box.New(Orientation.Horizontal, 8);
        var wrLbl = Label.New("W 0 B/s"); wrLbl.AddCssClass("rate-tx");
        wrLbl.Halign = Align.Start; wrLbl.Hexpand = true;
        var wrBar = LevelBar.New(); wrBar.Hexpand = true;
        wrRow.Append(wrLbl); wrRow.Append(wrBar);
        card.Append(wrRow);
        _container.Append(card);
        return new DevState(rdLbl, wrLbl, rdBar, wrBar,
                            new Queue<double>(60), new Queue<double>(60));
    }

    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        if (_timerId != 0) { GLib.Functions.SourceRemove(_timerId); _timerId = 0; }
    }

    private static void Enqueue(Queue<double> q, double v)
    { if (q.Count >= 60) q.Dequeue(); q.Enqueue(v); }
}
