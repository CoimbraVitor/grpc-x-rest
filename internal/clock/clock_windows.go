//go:build windows

package clock

import (
	"syscall"
	"unsafe"
)

var (
	kernel32                    = syscall.NewLazyDLL("kernel32.dll")
	procQueryPerformanceCounter = kernel32.NewProc("QueryPerformanceCounter")
	procQueryPerformanceFreq    = kernel32.NewProc("QueryPerformanceFrequency")
	qpcFreqMs                   float64
)

func init() {
	var freq int64
	_, _, _ = procQueryPerformanceFreq.Call(uintptr(unsafe.Pointer(&freq)))
	if freq > 0 {
		qpcFreqMs = float64(freq) / 1000.0
	} else {
		qpcFreqMs = 1.0
	}
}

// Now returns the current high-resolution hardware performance counter tick.
func Now() int64 {
	var counter int64
	_, _, _ = procQueryPerformanceCounter.Call(uintptr(unsafe.Pointer(&counter)))
	return counter
}

// SinceMs returns elapsed time in milliseconds since start using QPC (typically ~0.1 us resolution).
func SinceMs(start int64) float64 {
	end := Now()
	return float64(end-start) / qpcFreqMs
}
