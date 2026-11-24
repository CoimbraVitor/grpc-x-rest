//go:build !windows

package clock

import "time"

// Now returns a monotonic timestamp (on macOS/Linux Go uses mach_absolute_time / clock_gettime
// with nanosecond monotonic resolution).
func Now() time.Time {
	return time.Now()
}

// SinceMs returns elapsed time in milliseconds since start using Go's monotonic clock.
func SinceMs(start time.Time) float64 {
	return float64(time.Since(start).Nanoseconds()) / 1e6
}
