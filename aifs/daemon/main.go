package main

import (
"encoding/json"
"fmt"
"log"
"net"
"os"
"os/signal"
"syscall"
)

const (
VERSION = "0.1.0"
SOCKET  = "/run/aimos/aifs-daemon.sock"
)

type Request struct {
Op   string `json:"op"`
Path string `json:"path"`
Name string `json:"name"`
Snap string `json:"snap"`
}

type Response struct {
OK    bool        `json:"ok"`
Error string      `json:"error,omitempty"`
Data  interface{} `json:"data,omitempty"`
}

func handle(conn net.Conn) {
defer conn.Close()
var req Request
if err := json.NewDecoder(conn).Decode(&req); err != nil {
writeResp(conn, Response{Error: "bad request: " + err.Error()})
return
}
var resp Response
switch req.Op {
case "create_volume":
vol, err := CreateVolume(req.Path)
if err != nil { resp = Response{Error: err.Error()} } else { resp = Response{OK: true, Data: vol} }
case "delete_volume":
if err := DeleteVolume(req.Path); err != nil { resp = Response{Error: err.Error()} } else { resp = Response{OK: true} }
case "list_volumes":
vols, err := ListVolumes(req.Path)
if err != nil { resp = Response{Error: err.Error()} } else { resp = Response{OK: true, Data: vols} }
case "snapshot":
snap, err := TakeSnapshot(req.Path, req.Name)
if err != nil { resp = Response{Error: err.Error()} } else { resp = Response{OK: true, Data: snap} }
case "list_snapshots":
snaps, err := ListSnapshots(req.Path)
if err != nil { resp = Response{Error: err.Error()} } else { resp = Response{OK: true, Data: snaps} }
case "restore":
if err := RestoreSnapshot(req.Snap, req.Path); err != nil { resp = Response{Error: err.Error()} } else { resp = Response{OK: true} }
case "delete_snapshot":
if err := DeleteSnapshot(req.Snap); err != nil { resp = Response{Error: err.Error()} } else { resp = Response{OK: true} }
default:
resp = Response{Error: fmt.Sprintf("unknown op: %s", req.Op)}
}
writeResp(conn, resp)
}

func writeResp(conn net.Conn, r Response) {
_ = json.NewEncoder(conn).Encode(r)
}

func main() {
log.SetPrefix("[aimos-aifs] ")
log.Printf("AIFS daemon v%s starting", VERSION)
os.MkdirAll("/run/aimos", 0755)
os.Remove(SOCKET)
ln, err := net.Listen("unix", SOCKET)
if err != nil {
log.Fatalf("listen: %v", err)
}
defer ln.Close()
log.Printf("listening on %s", SOCKET)
go func() {
for {
conn, err := ln.Accept()
if err != nil { return }
go handle(conn)
}
}()
sig := make(chan os.Signal, 1)
signal.Notify(sig, syscall.SIGTERM, syscall.SIGINT)
<-sig
log.Println("shutting down")
}
