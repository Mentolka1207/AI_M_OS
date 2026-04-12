package main

import (
	"encoding/json"
	"log"
	"net"
	"os"
	"time"
)

const socketPath = "/run/aimos/network-daemon.sock"

type NetMetrics struct {
	Timestamp int64             `json:"timestamp"`
	Ifaces    map[string]IfaceStats `json:"ifaces"`
}

type IfaceStats struct {
	RxBytesPerSec float64 `json:"rx_bps"`
	TxBytesPerSec float64 `json:"tx_bps"`
}

func main() {
	os.MkdirAll("/run/aimos", 0755)
	os.Remove(socketPath)

	ln, err := net.Listen("unix", socketPath)
	if err != nil {
		log.Fatalf("listen: %v", err)
	}
	defer ln.Close()
	log.Printf("network-daemon listening on %s", socketPath)

	for {
		conn, err := ln.Accept()
		if err != nil {
			log.Printf("accept: %v", err)
			continue
		}
		go handleConn(conn)
	}
}

func handleConn(conn net.Conn) {
	defer conn.Close()
	metrics := collectMetrics()
	json.NewEncoder(conn).Encode(metrics)
}

// Reads /proc/net/dev — same source as C# monitor
func collectMetrics() NetMetrics {
	// Simplified: real implementation diffs two snapshots
	return NetMetrics{
		Timestamp: time.Now().Unix(),
		Ifaces:    readProcNetDev(),
	}
}
