package main

import (
"fmt"
"os"
"os/exec"
"path/filepath"
"strings"
"time"
)

const snapshotDir = ".aifs-snapshots"

type Volume struct {
Path      string `json:"path"`
CreatedAt string `json:"created_at"`
}

type Snapshot struct {
Name      string `json:"name"`
Path      string `json:"path"`
Volume    string `json:"volume"`
CreatedAt string `json:"created_at"`
ReadOnly  bool   `json:"read_only"`
}

func btrfsExec(args ...string) (string, error) {
cmd := exec.Command("btrfs", args...)
out, err := cmd.CombinedOutput()
return strings.TrimSpace(string(out)), err
}

func CreateVolume(path string) (*Volume, error) {
if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
return nil, fmt.Errorf("mkdir parent: %w", err)
}
out, err := btrfsExec("subvolume", "create", path)
if err != nil {
return nil, fmt.Errorf("btrfs subvolume create: %s: %w", out, err)
}
snapDir := filepath.Join(path, snapshotDir)
if err := os.MkdirAll(snapDir, 0755); err != nil {
return nil, fmt.Errorf("mkdir snapshots dir: %w", err)
}
return &Volume{Path: path, CreatedAt: time.Now().Format(time.RFC3339)}, nil
}

func DeleteVolume(path string) error {
out, err := btrfsExec("subvolume", "delete", path)
if err != nil {
return fmt.Errorf("btrfs subvolume delete: %s: %w", out, err)
}
return nil
}

func ListVolumes(rootPath string) ([]Volume, error) {
out, err := btrfsExec("subvolume", "list", "-o", rootPath)
if err != nil {
return nil, fmt.Errorf("btrfs subvolume list: %s: %w", out, err)
}
var vols []Volume
for _, line := range strings.Split(out, "\n") {
if line == "" {
continue
}
parts := strings.Fields(line)
if len(parts) < 9 {
continue
}
p := filepath.Join(rootPath, parts[8])
if strings.Contains(p, snapshotDir) {
continue
}
vols = append(vols, Volume{Path: p})
}
return vols, nil
}

func TakeSnapshot(volumePath, name string) (*Snapshot, error) {
if name == "" {
name = time.Now().Format("2006-01-02_15-04-05")
}
snapDir := filepath.Join(volumePath, snapshotDir)
if err := os.MkdirAll(snapDir, 0755); err != nil {
return nil, fmt.Errorf("mkdir snapshots: %w", err)
}
snapPath := filepath.Join(snapDir, name)
out, err := btrfsExec("subvolume", "snapshot", "-r", volumePath, snapPath)
if err != nil {
return nil, fmt.Errorf("btrfs snapshot: %s: %w", out, err)
}
return &Snapshot{
Name: name, Path: snapPath, Volume: volumePath,
CreatedAt: time.Now().Format(time.RFC3339), ReadOnly: true,
}, nil
}

func ListSnapshots(volumePath string) ([]Snapshot, error) {
snapDir := filepath.Join(volumePath, snapshotDir)
entries, err := os.ReadDir(snapDir)
if os.IsNotExist(err) {
return []Snapshot{}, nil
}
if err != nil {
return nil, fmt.Errorf("readdir: %w", err)
}
var snaps []Snapshot
for _, e := range entries {
if !e.IsDir() {
continue
}
info, _ := e.Info()
snaps = append(snaps, Snapshot{
Name: e.Name(), Path: filepath.Join(snapDir, e.Name()),
Volume: volumePath, CreatedAt: info.ModTime().Format(time.RFC3339),
ReadOnly: true,
})
}
return snaps, nil
}

func RestoreSnapshot(snapPath, volumePath string) error {
backup := volumePath + ".aifs-restore-backup"
if err := os.Rename(volumePath, backup); err != nil {
return fmt.Errorf("rename volume to backup: %w", err)
}
out, err := btrfsExec("subvolume", "snapshot", snapPath, volumePath)
if err != nil {
_ = os.Rename(backup, volumePath)
return fmt.Errorf("btrfs snapshot restore: %s: %w", out, err)
}
if out, err := btrfsExec("subvolume", "delete", backup); err != nil {
return fmt.Errorf("delete backup: %s: %w", out, err)
}
return nil
}

func DeleteSnapshot(snapPath string) error {
out, err := btrfsExec("subvolume", "delete", snapPath)
if err != nil {
return fmt.Errorf("btrfs snapshot delete: %s: %w", out, err)
}
return nil
}

func VolumeExists(path string) bool {
out, err := btrfsExec("subvolume", "show", path)
return err == nil && out != ""
}
