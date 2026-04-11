import GLib from 'gi://GLib';
import Gio from 'gi://Gio';
import * as St from 'gi://St';

let _stylesheet = null;

export default class AiMOSGlass {
    enable() {
        const theme = St.ThemeContext.get_for_stage(global.stage).get_theme();
        _stylesheet = Gio.File.new_for_path(
            GLib.build_filenamev([GLib.get_home_dir(),
            '.local/share/gnome-shell/extensions/aimos-glass@aimos/style.css'])
        );
        theme.load_stylesheet(_stylesheet);
    }
    disable() {
        if (_stylesheet) {
            const theme = St.ThemeContext.get_for_stage(global.stage).get_theme();
            theme.unload_stylesheet(_stylesheet);
            _stylesheet = null;
        }
    }
}
