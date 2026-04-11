// AI_M_OS — Power Daemon
// Управление питанием: батарея, suspend, CPU governor
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"syscall"
	"time"
)

const (
	VERSION    = "0.1.0"
	SOCKET_PATH = "/run/aimos/power.sock"
)

type PowerState struct {
	CPUGovernor   string  `json:"cpu_governor"`
	CPUFreqMHz    int     `json:"cpu_freq_mhz"`
	CPUUsage      float64 `json:"cpu_usage"`
	MemTotalMB    int     `json:"mem_total_mb"`
	MemUsedMB     int     `json:"mem_used_mb"`
	MemUsedPct    float64 `json:"mem_used_pct"`
	UptimeSeconds int64   `json:"uptime_seconds"`
	Timestamp     string  `json:"timestamp"`
}

func readFile(path string) string {
	data, err := os.ReadFile(path)
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(data))
}

func getCPUGovernor() string {
	gov := readFile("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
	if gov == "" {
		return "unknown"
	}
	return gov
}

func getCPUFreq() int {
	freq := readFile("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq")
	if freq == "" {
		return 0
	}
	khz, err := strconv.Atoi(freq)
	if err != nil {
		return 0
	}
	return khz / 1000
}

func getMemInfo() (int, int, float64) {
	data, err := os.ReadFile("/proc/meminfo")
	if err != nil {
		return 0, 0, 0
	}
	mem := make(map[string]int)
	for _, line := range strings.Split(string(data), "\n") {
		parts := strings.Fields(line)
		if len(parts) >= 2 {
			key := strings.TrimSuffix(parts[0], ":")
			val, _ := strconv.Atoi(parts[1])
			mem[key] = val
		}
	}
	total := mem["MemTotal"] / 1024
	avail := mem["MemAvailable"] / 1024
	used := total - avail
	pct := 0.0
	if total > 0 {
		pct = float64(used) / float64(total) * 100
	}
	return total, used, pct
}

func getUptime() int64 {
	data := readFile("/proc/uptime")
	if data == "" {
		return 0
	}
	parts := strings.Fields(data)
	if len(parts) == 0 {
		return 0
	}
	f, err := strconv.ParseFloat(parts[0], 64)
	if err != nil {
		return 0
	}
	return int64(f)
}

func setCPUGovernor(gov string) error {
	cpus, err := os.ReadDir("/sys/devices/system/cpu")
	if err != nil {
		return err
	}
	for _, cpu := range cpus {
		if !strings.HasPrefix(cpu.Name(), "cpu") {
			continue
		}
		path := fmt.Sprintf("/sys/devices/system/cpu/%s/cpufreq/scaling_governor", cpu.Name())
		if _, err := os.Stat(path); err == nil {
			if err := os.WriteFile(path, []byte(gov), 0644); err != nil {
				log.Printf("[WARN] Cannot set governor for %s: %v", cpu.Name(), err)
			}
		}
	}
	return nil
}

func collectState() PowerState {
	total, used, pct := getMemInfo()
	return PowerState{
		CPUGovernor:   getCPUGovernor(),
		CPUFreqMHz:    getCPUFreq(),
		MemTotalMB:    total,
		MemUsedMB:     used,
		MemUsedPct:    pct,
		UptimeSeconds: getUptime(),
		Timestamp:     time.Now().Format(time.RFC3339),
	}
}

func writeState(state PowerState) {
	os.MkdirAll("/run/aimos", 0755)
	data, err := json.Marshal(state)
	if err != nil {
		return
	}
	os.WriteFile("/run/aimos/power-state.json", data, 0644)
}

func main() {
	log.SetPrefix("[AI_M_OS power-daemon] ")
	log.Printf("Starting v%s", VERSION)

	// Установи производительный governor по умолчанию
	if err := setCPUGovernor("schedutil"); err != nil {
		log.Printf("Cannot set CPU governor: %v", err)
	}

	// Graceful shutdown
	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGTERM, syscall.SIGINT)

	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			state := collectState()
			writeState(state)
			log.Printf("cpu=%s %dMHz mem=%d/%dMB (%.1f%%) uptime=%ds",
				state.CPUGovernor, state.CPUFreqMHz,
				state.MemUsedMB, state.MemTotalMB,
				state.MemUsedPct, state.UptimeSeconds)
		case <-sig:
			log.Println("Shutting down...")
			os.Remove("/run/aimos/power-state.json")
			return
		}
	}
}
