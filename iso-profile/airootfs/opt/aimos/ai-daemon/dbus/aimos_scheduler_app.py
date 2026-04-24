#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dbus
import dbus.mainloop.glib
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib

BUS_NAME = 'org.aimos.Scheduler'
OBJ_PATH = '/org/aimos/Scheduler'
IFACE    = 'org.aimos.Scheduler'


def get_proxy():
    try:
        bus = dbus.SystemBus()
        return bus.get_object(BUS_NAME, OBJ_PATH)
    except dbus.DBusException as e:
        return None


def list_processes():
    procs = []
    for entry in os.scandir('/proc'):
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        try:
            name = open(f'/proc/{pid}/comm').read().strip()
            nice = os.getpriority(os.PRIO_PROCESS, pid)
            procs.append((pid, name, nice))
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            pass
    return sorted(procs, key=lambda x: x[0])


class SchedulerWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title('AI_M_OS Scheduler')
        self.set_default_size(600, 700)

        self._proxy = get_proxy()

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Header
        header = Adw.HeaderBar()
        box.append(header)

        # Status bar
        self._status_label = Gtk.Label()
        self._status_label.set_margin_top(8)
        self._status_label.set_margin_bottom(4)
        self._update_status()
        box.append(self._status_label)

        # Refresh button
        refresh_btn = Gtk.Button(label='Refresh')
        refresh_btn.set_margin_start(12)
        refresh_btn.set_margin_end(12)
        refresh_btn.set_margin_bottom(8)
        refresh_btn.connect('clicked', self._on_refresh)
        box.append(refresh_btn)

        # Process list
        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self._list_box = Gtk.ListBox()
        self._list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._list_box.add_css_class('boxed-list')
        self._list_box.set_margin_start(12)
        self._list_box.set_margin_end(12)
        scroll.set_child(self._list_box)
        box.append(scroll)

        # Nice control panel
        panel = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        panel.set_margin_top(8)
        panel.set_margin_bottom(12)
        panel.set_margin_start(12)
        panel.set_margin_end(12)

        self._nice_spin = Gtk.SpinButton()
        self._nice_spin.set_range(-20, 19)
        self._nice_spin.set_increments(1, 5)
        self._nice_spin.set_value(0)

        apply_btn = Gtk.Button(label='Set Priority')
        apply_btn.add_css_class('suggested-action')
        apply_btn.connect('clicked', self._on_apply)

        self._result_label = Gtk.Label(label='')
        self._result_label.set_hexpand(True)
        self._result_label.set_halign(Gtk.Align.END)

        panel.append(Gtk.Label(label='Nice value:'))
        panel.append(self._nice_spin)
        panel.append(apply_btn)
        panel.append(self._result_label)
        box.append(panel)

        self.set_content(box)
        self._load_processes()

    def _update_status(self):
        if self._proxy is None:
            self._status_label.set_text('D-Bus: not connected  |  Kernel module: unknown')
            return
        try:
            loaded = self._proxy.IsKernelModuleLoaded(dbus_interface=IFACE)
            km = 'loaded' if loaded else 'not loaded'
            self._status_label.set_text(f'D-Bus: connected  |  Kernel module: {km}')
        except dbus.DBusException:
            self._status_label.set_text('D-Bus: error')

    def _load_processes(self):
        while True:
            row = self._list_box.get_row_at_index(0)
            if row is None:
                break
            self._list_box.remove(row)

        for pid, name, nice in list_processes():
            row = Adw.ActionRow()
            row.set_title(f'{name}')
            row.set_subtitle(f'PID: {pid}  |  Nice: {nice}')
            row.set_activatable(True)
            row._pid = pid
            row._nice = nice
            self._list_box.append(row)

    def _on_refresh(self, btn):
        self._update_status()
        self._load_processes()
        self._result_label.set_text('Refreshed')

    def _on_apply(self, btn):
        row = self._list_box.get_selected_row()
        if row is None:
            self._result_label.set_text('Select a process first')
            return
        pid  = row._pid
        nice = int(self._nice_spin.get_value())
        if self._proxy is None:
            self._result_label.set_text('D-Bus not connected')
            return
        try:
            ok = self._proxy.SetProcessPriority(pid, nice, dbus_interface=IFACE)
            if ok:
                self._result_label.set_text(f'PID {pid} -> nice {nice}: OK')
                self._load_processes()
            else:
                self._result_label.set_text(f'PID {pid}: failed')
        except dbus.DBusException as e:
            self._result_label.set_text(f'D-Bus error: {e.get_dbus_message()}')


class SchedulerApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='org.aimos.SchedulerApp')

    def do_activate(self):
        win = SchedulerWindow(self)
        win.present()


if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    app = SchedulerApp()
    sys.exit(app.run(sys.argv))