import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib
from scheduler.kernel_iface import renice_via_kernel, is_kernel_module_loaded

BUS_NAME = "org.aimos.Scheduler"
OBJ_PATH = "/org/aimos/Scheduler"
IFACE    = "org.aimos.Scheduler"
VERSION  = "0.5.0"


class SchedulerService(dbus.service.Object):

    @dbus.service.method(IFACE, in_signature='ii', out_signature='b')
    def SetProcessPriority(self, pid, nice):
        if not (-20 <= int(nice) <= 19):
            return False
        old = self._get_nice(int(pid))
        result = renice_via_kernel(int(pid), int(nice))
        if result:
            self.PriorityChanged(int(pid), old, int(nice))
        return result

    @dbus.service.method(IFACE, in_signature='i', out_signature='i')
    def GetProcessPriority(self, pid):
        return self._get_nice(int(pid))

    @dbus.service.method(IFACE, out_signature='b')
    def IsKernelModuleLoaded(self):
        return is_kernel_module_loaded()

    @dbus.service.signal(IFACE, signature='iii')
    def PriorityChanged(self, pid, old_nice, new_nice):
        pass

    @dbus.service.method('org.freedesktop.DBus.Properties',
                         in_signature='ss', out_signature='v')
    def Get(self, interface, prop):
        if prop == 'Version':
            return VERSION
        raise dbus.exceptions.DBusException('Unknown property')

    def _get_nice(self, pid):
        try:
            return os.getpriority(os.PRIO_PROCESS, pid)
        except (ProcessLookupError, PermissionError):
            return 0


if __name__ == "__main__":
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    name = dbus.service.BusName(BUS_NAME, bus)
    svc  = SchedulerService(bus, OBJ_PATH)
    print(f"[aimos-scheduler] D-Bus service running on {BUS_NAME}")
    GLib.MainLoop().run()
