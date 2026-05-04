import GLib from 'gi://GLib';
import Gio  from 'gi://Gio';
import St   from 'gi://St';
import GObject from 'gi://GObject';
import Clutter from 'gi://Clutter';

import { Extension }  from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main      from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';

const SCHEDULER_IFACE_XML = `
<node>
  <interface name="org.aimos.Scheduler">
    <method name="IsKernelModuleLoaded">
      <arg type="b" direction="out" name="loaded"/>
    </method>
    <method name="SetProcessPriority">
      <arg type="i" direction="in"  name="pid"/>
      <arg type="i" direction="in"  name="nice"/>
      <arg type="b" direction="out" name="ok"/>
    </method>
    <signal name="PriorityChanged">
      <arg type="i" name="pid"/>
      <arg type="i" name="old_nice"/>
      <arg type="i" name="new_nice"/>
    </signal>
    <property name="Version" type="s" access="read"/>
  </interface>
</node>`;

const BUS_NAME = 'org.aimos.Scheduler';
const OBJ_PATH = '/org/aimos/Scheduler';
const POLL_SEC = 3;

const SchedulerProxy = Gio.DBusProxy.makeProxyWrapper(SCHEDULER_IFACE_XML);

const SchedulerIndicator = GObject.registerClass(
class SchedulerIndicator extends PanelMenu.Button {

    _init(extensionPath) {
        super._init(0.0, 'AI_M_OS Scheduler');
        this._extensionPath = extensionPath;

        this._label = new St.Label({
            text: '[] ...',
            y_align: Clutter.ActorAlign.CENTER,
        });
        this.add_child(this._label);

        this._statusItem  = new PopupMenu.PopupMenuItem('Status: connecting...', { reactive: false });
        this._lastItem    = new PopupMenu.PopupMenuItem('LAST: -',             { reactive: false });
        this._versionItem = new PopupMenu.PopupMenuItem('',                    { reactive: false });

        this.menu.addMenuItem(this._statusItem);
        this.menu.addMenuItem(this._lastItem);
        this.menu.addMenuItem(this._versionItem);
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        const openItem = new PopupMenu.PopupMenuItem('Open Scheduler App');
        openItem.connect('activate', () => this._openApp());
        this.menu.addMenuItem(openItem);

        this._proxy      = null;
        this._signalId   = null;
        this._pollSource = null;

       this._connectProxy();
    }

    _connectProxy() {
        try {
            this._proxy = new SchedulerProxy(
                Gio.DBus.system, BUS_NAME, OBJ_PATH,
                (proxy, error) => {
                    if (error) { this._setOffline(); return; }
                    this._signalId = this._proxy.connectSignal(
                        'PriorityChanged',
                        (_p, _s, [pid, oldNice, newNice]) => {
                            this._lastItem.label.set_text(
                                `Last: pid ${pid}  ${oldNice} -> ${newNice}`);
                        }
                    );
                    this._startPolling();
                }
            );
        } catch (_e) { this._setOffline(); }
    }

    _startPolling() {
        this._poll();
        this._pollSource = GLib.timeout_add_seconds(
            GLib.PRIORITY_DEFAULT, POLL_SEC,
            () => { this._poll(); return GLib.SOURCE_CONTINUE; }
        );
    }

   _poll() {
        if (!this._proxy) { this._setOffline(); return; }
        try {
            this._proxy.IsKernelModuleLoadedRemote((result, error) => {
                if (error) { this._setOffline(); return; }
                const loaded = result[0];
                this._label.set_text(loaded ? '[] ACTIVE' : '[] IDLE');
                this._statusItem.label.set_text(
                    loaded ? 'Status: kernel module ACTIVE'
                           : 'Status: daemon running, module absent');
                try {
                    const ver = this._proxy.Version;
                    if (ver) this._versionItem.label.set_text(`Version: ${ver}`);
                } catch (_) {}
            });
        } catch (_e) { this._setOffline(); }
    }

    _setOffline() {
       this._label.set_text('X OFFLINE');
       this._statusItem.label.set_text('Status: D-Bus service unavailable');
    }

    _openApp() {
        try {
            GLib.spawn_async(null,
                ['/usr/bin/python3',
                 '/home/aimos/AI_M_OS/ai-daemon/dbus/aimos_scheduler_app.py'],
                null,
                GLib.SpawnFlags.SEARCH_PATH | GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                null);
        } catch (e) {
            Main.notifyError('AI_M_OS', `Cannot open app: ${e.message}`);
        }
    }

    destroy() {
        if (this._pollSource) {
            GLib.source_remove(this._pollSource);
            this._pollSource = null;
        }
        if (this._signalId && this._proxy)
            this._proxy.disconnectSignal(this._signalId);
        super.destroy();
    }
});

export default class AimosSchedulerExtension extends Extension {
    enable() {
        this._indicator = new SchedulerIndicator(this.path);
        Main.panel.addToStatusArea(this.uuid, this._indicator, 1, 'right');
    }
    disable() {
        this._indicator?.destroy();
        this._indicator = null;
    }
}
