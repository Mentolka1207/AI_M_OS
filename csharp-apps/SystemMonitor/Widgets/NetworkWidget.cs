using Gtk;
using AI_M_OS.SystemMonitor.Services;

namespace AI_M_OS.SystemMonitor.Widgets;

public class NetworkWidget : IDisposable
{
    private const uint PollMs = 1000;
    private record IfaceState(Label RxLabel, Label TxLabel,
                               LevelBar RxBar, LevelBar TxBar,
                               Queue<double> RxH, Queue<double> TxH);
    private readonly Dictionary<string, IfaceState> _ifaces = new();
    private readonly Box _container;
    private List<NetSnapshot> _prev = [];
    private uint _timerId;
    private bool _disposed;

    public Widget Root => _container;

    public NetworkWidget()
    {
        _container = Box.New(Orientation.Vertical, 8);
        var title = Label.New("o  NETWORK I/O");
        title.AddCssClass("section-title");
        title.Halign = Align.Start;
        _container.Append(title);
      _prev = [..SystemMetrics.ReadNetSnapshots()];
        _timerId = GLib.Functions.TimeoutAdd(0, PollMs, Tick);
    }

    private bool Tick()
    {
        try
        {
            var curr = SystemMetrics.ReadNetSnapshots();
            foreach (var s in curr)
            {
                var p = _prev.Find(x => x.Iface == s.Iface); if (p is null) continue;
                var r = SystemMetrics.ComputeNetRate(p, s);   if (r is null) continue;
                if (!_ifaces.TryGetValue(s.Iface, out var st))
                { st = MakeRow(s.Iface); _ifaces[s.Iface] = st; }
                Enqueue(st.RxH, r.ReadBytesPerSec);
                Enqueue(st.TxH, r.WriteBytesPerSec);
                st.RxLabel.SetText("v " + SystemMetrics.FormatRate(r.ReadBytesPerSec));
                st.TxLabel.SetText("^ " + SystemMetrics.FormatRate(r.WriteBytesPerSec));
                st.RxBar.Value = SystemMetrics.Normalize(r.ReadBytesPerSec, st.RxH.Max());
                st.TxBar.Value = SystemMetrics.Normalize(r.WriteBytesPerSec, st.TxH.Max());
            }
            _prev = [..curr];
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine("[NetworkWidget] Tick error: " + ex.Message);
        }
        return true;
    }

    private IfaceState MakeRow(string iface)
    {
        var card = Box.New(Orientation.Vertical, 6);
        card.AddCssClass("glass-card");
        var name = Label.New(iface.ToUpperInvariant());
        name.AddCssClass("iface-name");
        name.Halign = Align.Start;
        card.Append(name);
        var rxRow = Box.New(Orientation.Horizontal, 8);
        var rxLbl = Label.New("v 0 B/s");
        rxLbl.AddCssClass("rate-rx");
        rxLbl.Halign = Align.Start;
        rxLbl.Hexpand = true;
        var rxBar = LevelBar.New();
        rxBar.Hexpand = true;
        rxRow.Append(rxLbl);
        rxRow.Append(rxBar);
        card.Append(rxRow);
        var txRow = Box.New(Orientation.Horizontal, 8);
        var txLbl = Label.New("^ 0 B/s");
        txLbl.AddCssClass("rate-tx");
        txLbl.Halign = Align.Start;
        txLbl.Hexpand = true;
        var txBar = LevelBar.New();
        txBar.Hexpand = true;
        txRow.Append(txLbl);
        txRow.Append(txBar);
        card.Append(txRow);
        _container.Append(card);
        return new IfaceState(rxLbl, txLbl, rxBar, txBar,
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