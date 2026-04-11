// AI_M_OS — Network Daemon
// Мониторинг сети: интерфейсы, трафик, DNS
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"syscall"
	"time"
)

const VERSION = "0.1.0"

type InterfaceStats struct {
	Name      string `json:"name"`
	IPAddr    string `json:"ip_addr"`
	RxBytes   uint64 `json:"rx_bytes"`
	TxBytes   uint64 `json:"tx_bytes"`
	RxBytesPS uint64 `json:"rx_bytes_per_sec"`
	TxBytesPS uint64 `json:"tx_bytes_per_sec"`
	IsUp      bool   `json:"is_up"`
}

type NetworkState struct {
	Interfaces []InterfaceStats `json:"interfaces"`
	Hostname   string           `json:"hostname"`
	Timestamp  string           `json:"timestamp"`
}

type ifaceCounter struct {
	rx, tx uint64
}

var prevCounters = make(map[string]ifaceCounter)

func parseNetDev() map[string]ifaceCounter {
	data, err := os.ReadFile("/proc/net/dev")
	if err != nil {
		return nil
	}
	result := make(map[string]ifaceCounter)
	for _, line := range strings.Split(string(data), "\n")[2:] {
		parts := strings.Fields(strings.TrimSpace(line))
		if len(parts) < 10 {
			continue
		}
		name := strings.TrimSuffix(parts[0], ":")
		rx, _ := strconv.ParseUint(parts[1], 10, 64)
		tx, _ := strconv.ParseUint(parts[9], 10, 64)
		result[name] = ifaceCounter{rx, tx}
	}
	return result
}

func getInterfaces() []InterfaceStats {
	ifaces, err := net.Interfaces()
	if err != nil {
		return nil
	}
	counters := parseNetDev()
	var result []InterfaceStats

	for _, iface := range ifaces {
		if iface.Name == "lo" {
			continue
		}
		ip := ""
		addrs, _ := iface.Addrs()
		for _, addr := range addrs {
			if ipnet, ok := addr.(*net.IPNet); ok && ipnet.IP.To4() != nil {
				ip = ipnet.IP.String()
				break
			}
		}

		isUp := iface.Flags&net.FlagUp != 0
		cur := counters[iface.Name]
		prev := prevCounters[iface.Name]

		rxPS := uint64(0)
		txPS := uint64(0)
		if prev.rx > 0 && cur.rx >= prev.rx {
			rxPS = (cur.rx - prev.rx) / 5
			txPS = (cur.tx - prev.tx) / 5
		}
		prevCounters[iface.Name] = cur

		result = append(result, InterfaceStats{
			Name:      iface.Name,
			IPAddr:    ip,
			RxBytes:   cur.rx,
			TxBytes:   cur.tx,
			RxBytesPS: rxPS,
			TxBytesPS: txPS,
			IsUp:      isUp,
		})
	}
	return result
}

func collectState() NetworkState {
	hostname, _ := os.Hostname()
	return NetworkState{
		Interfaces: getInterfaces(),
		Hostname:   hostname,
		Timestamp:  time.Now().Format(time.RFC3339),
	}
}

func writeState(state NetworkState) {
	os.MkdirAll("/run/aimos", 0755)
	data, err := json.Marshal(state)
	if err != nil {
		return
	}
	os.WriteFile("/run/aimos/network-state.json", data, 0644)
}

func main() {
	log.SetPrefix("[AI_M_OS network-daemon] ")
	log.Printf("Starting v%s", VERSION)

	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGTERM, syscall.SIGINT)

	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			state := collectState()
			writeState(state)
			for _, iface := range state.Interfaces {
				if iface.IsUp {
					fmt.Printf("[AI_M_OS network-daemon] %s ip=%s rx=%d tx=%d B/s\n",
						iface.Name, iface.IPAddr, iface.RxBytesPS, iface.TxBytesPS)
				}
			}
		case <-sig:
			log.Println("Shutting down...")
			os.Remove("/run/aimos/network-state.json")
			return
		}
	}
}
