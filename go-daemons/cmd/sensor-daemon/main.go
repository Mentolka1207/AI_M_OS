// AI_M_OS — Sensor Daemon
// Температура CPU, нагрузка, дисковая активность
package main

import (
	"encoding/json"
	"log"
	"os"
	"os/signal"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
	"time"
)

const VERSION = "0.1.0"

type SensorState struct {
	CPUTempC    float64            `json:"cpu_temp_c"`
	LoadAvg1    float64            `json:"load_avg_1min"`
	LoadAvg5    float64            `json:"load_avg_5min"`
	LoadAvg15   float64            `json:"load_avg_15min"`
	DiskStats   map[string]uint64  `json:"disk_io_ops"`
	Timestamp   string             `json:"timestamp"`
}

func getCPUTemp() float64 {
	// Ищем температуру в hwmon
	matches, err := filepath.Glob("/sys/class/hwmon/hwmon*/temp*_input")
	if err != nil || len(matches) == 0 {
		// fallback: thermal zones
		zones, _ := filepath.Glob("/sys/class/thermal/thermal_zone*/temp")
		for _, z := range zones {
			data, err := os.ReadFile(z)
			if err != nil {
				continue
			}
			val, err := strconv.ParseFloat(strings.TrimSpace(string(data)), 64)
			if err == nil && val > 1000 {
				return val / 1000.0
			}
		}
		return 0
	}
	for _, m := range matches {
		data, err := os.ReadFile(m)
		if err != nil {
			continue
		}
		val, err := strconv.ParseFloat(strings.TrimSpace(string(data)), 64)
		if err == nil && val > 1000 {
			return val / 1000.0
		}
	}
	return 0
}

func getLoadAvg() (float64, float64, float64) {
	data, err := os.ReadFile("/proc/loadavg")
	if err != nil {
		return 0, 0, 0
	}
	parts := strings.Fields(string(data))
	if len(parts) < 3 {
		return 0, 0, 0
	}
	l1, _ := strconv.ParseFloat(parts[0], 64)
	l5, _ := strconv.ParseFloat(parts[1], 64)
	l15, _ := strconv.ParseFloat(parts[2], 64)
	return l1, l5, l15
}

func getDiskStats() map[string]uint64 {
	data, err := os.ReadFile("/proc/diskstats")
	if err != nil {
		return nil
	}
	result := make(map[string]uint64)
	for _, line := range strings.Split(string(data), "\n") {
		parts := strings.Fields(line)
		if len(parts) < 14 {
			continue
		}
		name := parts[2]
		if strings.HasPrefix(name, "sd") || strings.HasPrefix(name, "nvme") {
			ios, _ := strconv.ParseUint(parts[3], 10, 64)
			result[name] = ios
		}
	}
	return result
}

func collectState() SensorState {
	l1, l5, l15 := getLoadAvg()
	return SensorState{
		CPUTempC:  getCPUTemp(),
		LoadAvg1:  l1,
		LoadAvg5:  l5,
		LoadAvg15: l15,
		DiskStats: getDiskStats(),
		Timestamp: time.Now().Format(time.RFC3339),
	}
}

func main() {
	log.SetPrefix("[AI_M_OS sensor-daemon] ")
	log.Printf("Starting v%s", VERSION)

	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGTERM, syscall.SIGINT)
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			state := collectState()
			os.MkdirAll("/run/aimos", 0755)
			data, _ := json.Marshal(state)
			os.WriteFile("/run/aimos/sensor-state.json", data, 0644)
			log.Printf("temp=%.1f°C load=%.2f/%.2f/%.2f",
				state.CPUTempC, state.LoadAvg1, state.LoadAvg5, state.LoadAvg15)
		case <-sig:
			log.Println("Shutting down...")
			return
		}
	}
}
