#!/usr/bin/env python3
import json, socket, sys, os
from datetime import datetime

SOCKET_PATH = "/run/aimos/aifs-daemon.sock"

def send(op, **kwargs):
    req = {"op": op, **kwargs}
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(10.0)
            s.connect(SOCKET_PATH)
            s.sendall(json.dumps(req).encode() + b"\n")
            data = b""
            while chunk := s.recv(4096):
                data += chunk
        return json.loads(data.decode())
    except FileNotFoundError:
        die("aifs-daemon is not running: systemctl start aimos-aifs")
    except Exception as e:
        die(f"socket error: {e}")

def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)

def ok(resp):
    if not resp.get("ok"):
        die(resp.get("error", "unknown error"))

def fmt_time(iso):
    try:
        return datetime.fromisoformat(iso).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso

def cmd_create(args):
    if not args: die("usage: aifs create <path>")
    resp = send("create_volume", path=args[0]); ok(resp)
    v = resp["data"]
    print(f"^ Volume created: {v['path']}\n  Created at:     {fmt_time(v['created_at'])}")

def cmd_delete(args):
    if not args: die("usage: aifs delete <path>")
    if input(f"Delete volume '{args[0]}'? [y/N] ").lower() != "y":
        print("Aborted."); return
    ok(send("delete_volume", path=args[0]))
    print(f"^ Deleted: {args[0]}")

def cmd_list(args):
    if not args: die("usage: aifs list <root>")
    resp = send("list_volumes", path=args[0]); ok(resp)
    vols = resp.get("data") or []
    if not vols: print("No volumes found."); return
    for v in vols: print(v["path"])

def cmd_snap(args):
    if not args: die("usage: aifs snap <volume> [name]")
    resp = send("snapshot", path=args[0], name=args[1] if len(args)>1 else ""); ok(resp)
    s = resp["data"]
    print(f"^ Snapshot: {s['name']}\n  Path:      {s['path']}\n  Created:   {fmt_time(s['created_at'])}")

def cmd_snaps(args):
    if not args: die("usage: aifs snaps <volume>")
    resp = send("list_snapshots", path=args[0]); ok(resp)
    snaps = resp.get("data") or []
    if not snaps: print("No snapshots."); return
    print(f"{'NAME':<30} {'CREATED':<20}")
    print("-" * 52)
    for s in snaps:
        print(f"{s['name']:<30} {fmt_time(s['created_at']):<20}")

def cmd_restore(args):
    if len(args) < 2: die("usage: aifs restore <volume> <snapshot>")
    if input(f"Restore '{args[0]}' from '{args[1]}'? [y/N] ").lower() != "y":
        print("Aborted."); return
    ok(send("restore", path=args[0], snap=args[1]))
    print(f"^ Restored: {args[0]}  <- {args[1]}")

def cmd_rmsnap(args):
    if not args: die("usage: aifs rmsnap <snapshot>")
    if input(f"Delete snapshot '{args[0]}'? [y/N] ").lower() != "y":
        print("Aborted."); return
    ok(send("delete_snapshot", snap=args[0]))
    print(f"^ Snapshot deleted: {args[0]}")

def cmd_help(_):
    print("Usage: aifs <command> [args]\n")
    print("  create  <path>             Create btrfs subvolume")
    print("  delete  <path>             Delete subvolume")
    print("  list    <root>             List subvolumes under root")
    print("  snap    <volume> [name]    Take read-only snapshot")
    print("  snaps   <volume>           List snapshots")
    print("  restore <volume> <snap>    Restore volume from snapshot")
    print("  rmsnap  <snapshot>         Delete snapshot")

COMMANDS = {
    "create": cmd_create, "delete": cmd_delete, "list": cmd_list,
    "snap": cmd_snap, "snaps": cmd_snaps, "restore": cmd_restore,
    "rmsnap": cmd_rmsnap, "help": cmd_help,
}

args = sys.argv[1:]
if not args or args[0] not in COMMANDS:
    cmd_help([]); sys.exit(0 if not args else 1)
COMMANDS[args[0]](args[1:])
