using Gtk;
using AI_M_OS.SystemMonitor.Services;

namespace AI_M_OS.SystemMonitor.Widgets;

/// <summary>
/// Displays real-time status of the aimos_scheduler kernel module
/// via /proc/aimos_scheduler.
///
/// Shows: module load status, total renice ops, last renice (pid + nice),
/// last error. Polls every 2 seconds.
/// </summary>
public class SchedulerWidget : IDisposable
{
    private const uint   PollMs      = 2000;
    private const string ProcIface   = "/proc/aimos_scheduler";

    // ── layout ──────────────────────────────────────────────────────────
    private readonly Box   _container;

    // status row
    private readonly Label _statusLabel;
    private readonly Label _versionLabel;

    // ops row
    private readonly Label   _totalOpsLabel;
    private readonly LevelBar _opsBar;          // visual pulse on new ops

    // last renice row
    private readonly Label _lastPidLabel;
    private readonly Label _lastNiceLabel;

    // error row
    private readonly Label _errorLabel;

    // polling
    private uint _timerId;
    private bool _disposed;
    private int  _prevTotalOps = -1;

    public Widget Root => _container;

    // ── constructor ──────────────────────────────────────────────────────
    public SchedulerWidget()
    {
        _container = Box.New(Orientation.Vertical, 8);

        var title = Label.New("󰒓  SCHEDULER");
        title.AddCssClass("section-title");
        title.Halign = Align.Start;
        _container.Append(title);

        var card = Box.New(Orientation.Vertical, 6);
        card.AddCssClass("glass-card");

        // ── row 1: module status + version ──────────────────────────────
        var statusRow = Box.New(Orientation.Horizontal, 8);

        _statusLabel = Label.New("● NOT LOADED");
        _statusLabel.AddCssClass("iface-name");
        _statusLabel.Halign = Align.Start;
        _statusLabel.Hexpand = true;

        _versionLabel = Label.New("");
        _versionLabel.AddCssClass("rate-rx");
        _versionLabel.Halign = Align.End;

        statusRow.Append(_statusLabel);
        statusRow.Append(_versionLabel);
        card.Append(statusRow);

        // ── row 2: total ops + bar ───────────────────────────────────────
        var opsRow = Box.New(Orientation.Horizontal, 8);

        _totalOpsLabel = Label.New("ops: 0");
        _totalOpsLabel.AddCssClass("rate-tx");
        _totalOpsLabel.Halign = Align.Start;
        _totalOpsLabel.Hexpand = true;

        _opsBar = LevelBar.New();
        _opsBar.Hexpand = true;
        _opsBar.MinValue = 0;
        _opsBar.MaxValue = 1;
        _opsBar.Value    = 0;

        opsRow.Append(_totalOpsLabel);
        opsRow.Append(_opsBar);
        card.Append(opsRow);

        // ── row 3: last renice pid + nice ────────────────────────────────
        var reniceRow = Box.New(Orientation.Horizontal, 8);

        _lastPidLabel = Label.New("pid: —");
        _lastPidLabel.AddCssClass("iface-name");
        _lastPidLabel.Halign = Align.Start;
        _lastPidLabel.Hexpand = true;

        _lastNiceLabel = Label.New("nice: —");
        _lastNiceLabel.AddCssClass("rate-rx");
        _lastNiceLabel.Halign = Align.End;

        reniceRow.Append(_lastPidLabel);
        reniceRow.Append(_lastNiceLabel);
        card.Append(reniceRow);

        // ── row 4: last error ────────────────────────────────────────────
        _errorLabel = Label.New("");
        _errorLabel.AddCssClass("rate-tx");
        _errorLabel.Halign = Align.Start;
        _errorLabel.Wrap   = true;
        card.Append(_errorLabel);

        _container.Append(card);

        _timerId = GLib.Functions.TimeoutAdd(0, PollMs, Tick);
    }

    // ── poll ─────────────────────────────────────────────────────────────
    private bool Tick()
    {
        try
        {
            if (!File.Exists(ProcIface))
            {
                _statusLabel.SetText("● NOT LOADED");
                _statusLabel.RemoveCssClass("rate-rx");
                _statusLabel.AddCssClass("rate-tx");
                _versionLabel.SetText("");
                _totalOpsLabel.SetText("ops: —");
                _lastPidLabel.SetText("pid: —");
                _lastNiceLabel.SetText("nice: —");
                _errorLabel.SetText("module not loaded");
                _opsBar.Value = 0;
                return true;
            }

            var info = ParseProcIface(File.ReadAllText(ProcIface));

            // status
            _statusLabel.SetText(info.Active ? "● ACTIVE" : "● INACTIVE");
            _statusLabel.RemoveCssClass(info.Active ? "rate-tx" : "rate-rx");
            _statusLabel.AddCssClass(info.Active ? "rate-rx" : "rate-tx");

            _versionLabel.SetText($"v{info.Version}");

            // ops — pulse bar briefly when a new op is detected
            _totalOpsLabel.SetText($"ops: {info.TotalOps}");
            bool newOp = _prevTotalOps >= 0 && info.TotalOps > _prevTotalOps;
            _opsBar.Value = newOp ? 1.0 : 0.0;
            _prevTotalOps = info.TotalOps;

            // last renice
            _lastPidLabel.SetText(info.LastPid >= 0 ? $"pid: {info.LastPid}" : "pid: —");
            _lastNiceLabel.SetText(info.LastPid >= 0 ? $"nice: {info.LastNice}" : "nice: —");

            // error
            _errorLabel.SetText(
                string.IsNullOrEmpty(info.LastError) || info.LastError == "none"
                    ? ""
                    : $"err: {info.LastError}");
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"[SchedulerWidget] Tick error: {ex.Message}");
        }

        return true;
    }

    // ── parser ────────────────────────────────────────────────────────────
    private static SchedulerInfo ParseProcIface(string raw)
    {
        var info = new SchedulerInfo();

        foreach (var line in raw.Split('\n', StringSplitOptions.RemoveEmptyEntries))
        {
            var idx = line.IndexOf(':');
            if (idx < 0) continue;

            var key   = line[..idx].Trim().ToLowerInvariant();
            var value = line[(idx + 1)..].Trim();

            switch (key)
            {
                case "status":
                    info.Active = value.Equals("active", StringComparison.OrdinalIgnoreCase);
                    break;
                case "version":
                    info.Version = value;
                    break;
                case "last_pid":
                    if (int.TryParse(value, out var pid))  info.LastPid  = pid;
                    break;
                case "last_nice":
                    if (int.TryParse(value, out var nice)) info.LastNice = nice;
                    break;
                case "total_ops":
                    if (int.TryParse(value, out var ops))  info.TotalOps = ops;
                    break;
                case "last_error":
                    info.LastError = value;
                    break;
            }
        }

        return info;
    }

    // ── data record ───────────────────────────────────────────────────────
    private sealed class SchedulerInfo
    {
        public bool   Active    { get; set; } = false;
        public string Version   { get; set; } = "?";
        public int    LastPid   { get; set; } = -1;
        public int    LastNice  { get; set; } = 0;
        public int    TotalOps  { get; set; } = 0;
        public string LastError { get; set; } = "";
    }

    // ── dispose ───────────────────────────────────────────────────────────
    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        if (_timerId != 0) { GLib.Functions.SourceRemove(_timerId); _timerId = 0; }
    }
}
