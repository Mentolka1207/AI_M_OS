package main

import (
	"bufio"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"
)

type snapshot struct {
	rx int64
	tx int64
	ts time.Time
}

var (
	mu        sync.Mutex
	prevSnaps = map[string]snapshot{}
)

func readProcNetDev() map[string]IfaceStats {
	f, err := os.Open("/proc/net/dev")
	if err != nil {
		return nil
	}
	defer f.Close()

	result := map[string]IfaceStats{}
	now := time.Now()
	scanner := bufio.NewScanner(f)
	lineNum := 0

	for scanner.Scan() {
		lineNum++
		if lineNum <= 2 {
			continue // skip headers
		}
		line := scanner.Text()
		colon := strings.Index(line, ":")
		if colon < 0 {
			continue
		}
		iface := strings.TrimSpace(line[:colon])
		if iface == "lo" {
			continue
		}
		fields := strings.Fields(line[colon+1:])
		if len(fields) < 9 {
			continue
		}
		rx, _ := strconv.ParseInt(fields[0], 10, 64)
		tx, _ := strconv.ParseInt(fields[8], 10, 64)

		mu.Lock()
		prev, ok := prevSnaps[iface]
		prevSnaps[iface] = snapshot{rx, tx, now}
		mu.Unlock()

		if ok {
			elapsed := now.Sub(prev.ts).Seconds()
			if elapsed > 0 {
				result[iface] = IfaceStats{
					RxBytesPerSec: float64(rx-prev.rx) / elapsed,
					TxBytesPerSec: float64(tx-prev.tx) / elapsed,
				}
			}
		} else {
			result[iface] = IfaceStats{}
		}
	}
	return result
}
