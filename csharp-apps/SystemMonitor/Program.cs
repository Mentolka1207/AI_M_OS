using Adw;
using AI_M_OS.SystemMonitor;

var app = Adw.Application.New(
    "io.github.mentolka1207.AiMOSSysmon",
    Gio.ApplicationFlags.FlagsNone);

app.OnActivate += (sender, _) =>
{
    var win = new MainWindow((Adw.Application)sender);
    win.Present();
};

return app.Run(0, null);
