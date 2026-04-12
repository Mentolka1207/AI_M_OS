using Gtk;
using AI_M_OS.SystemMonitor.Widgets;

namespace AI_M_OS.SystemMonitor;

public class MainWindow : Adw.ApplicationWindow
{
    public MainWindow(Adw.Application app) : base()
    {
        Application  = app;
        Title        = "AI_M_OS System Monitor";
        DefaultWidth = 440; DefaultHeight = 700;
        AddCssClass("aimos-monitor");
        LoadCss();

        var header = Adw.HeaderBar.New();
        header.AddCssClass("glass-header");
        header.TitleWidget = Label.New("System Monitor");

        var scroll = ScrolledWindow.New();
        scroll.Vexpand = true;
        scroll.HscrollbarPolicy = PolicyType.Never;

        var content = Box.New(Orientation.Vertical, 16);
        content.AddCssClass("content-box");
        content.Append(new NetworkWidget().Root);
        content.Append(new DiskWidget().Root);
        scroll.Child = content;

        var root = Box.New(Orientation.Vertical, 0);
        root.Append(header);
        root.Append(scroll);
        Content = root;
    }

    private static void LoadCss()
    {
        var provider = CssProvider.New();
        var cssPath  = Path.Combine(AppContext.BaseDirectory, "themes", "glassmorphism.css");
        if (File.Exists(cssPath))
            provider.LoadFromPath(cssPath);
        else
            provider.LoadFromString(
                "window.aimos-monitor{background:rgba(12,12,24,.82)}" +
                ".glass-card{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);border-radius:14px;padding:14px;margin-bottom:8px}" +
                ".section-title{font-size:10px;font-weight:700;letter-spacing:2px;color:rgba(255,255,255,.35)}" +
                ".iface-name{font-size:13px;font-weight:600;color:rgba(255,255,255,.88)}" +
                ".rate-rx{color:#33d9e0;font-size:12px;min-width:110px}" +
                ".rate-tx{color:#ff8c35;font-size:12px;min-width:110px}" +
                ".content-box{padding:20px 16px}");

        Gtk.StyleContext.AddProviderForDisplay(
            Gdk.Display.GetDefault()!,
            provider,
            Gtk.Constants.STYLE_PROVIDER_PRIORITY_APPLICATION);
    }
}
