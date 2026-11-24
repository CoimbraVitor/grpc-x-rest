package main

import (
	"crypto/tls"
	"encoding/json"
	"encoding/csv"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"strconv"
	"time"

	"grpc-x-rest/internal/clock"
	"grpc-x-rest/internal/dataset"
)

func main() {
	warmup := flag.Int("warmup", 100, "number of warm-up requests per payload size (discarded)")
	iterations := flag.Int("n", 1000, "number of measured requests per payload size")
	outPath := flag.String("out", filepath.Join("results", "raw_rest.csv"), "output CSV file path")
	flag.Parse()

	// Pre-build deterministic domain batches in memory so measurements isolate
	// serialization, HTTP/1.1 transport, and deserialization.
	batches := make(map[string]dataset.BatchResponse, len(dataset.DefaultSpecs))
	expectedCounts := make(map[string]int, len(dataset.DefaultSpecs))
	for _, spec := range dataset.DefaultSpecs {
		b, jsonSize := dataset.BuildBatch(spec)
		batches[spec.Label] = b
		expectedCounts[spec.Label] = len(b.Items)
		log.Printf("[REST] Prepared payload %s: %d items, %d JSON bytes", spec.Label, len(b.Items), jsonSize)
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/batch", func(w http.ResponseWriter, r *http.Request) {
		size := r.URL.Query().Get("size")
		batch, ok := batches[size]
		if !ok {
			http.Error(w, "unknown payload size", http.StatusBadRequest)
			return
		}
		payload, err := json.Marshal(batch)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		w.Header().Set("Content-Length", strconv.Itoa(len(payload)))
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write(payload)
	})

	// Explicit HTTP/1.1 server without TLS on loopback TCP.
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatalf("listen failed: %v", err)
	}
	srv := &http.Server{
		Handler:      mux,
		TLSNextProto: make(map[string]func(*http.Server, *tls.Conn, http.Handler)),
	}
	go func() {
		if err := srv.Serve(ln); err != nil && err != http.ErrServerClosed {
			log.Fatalf("REST server error: %v", err)
		}
	}()
	defer srv.Close()

	// Explicit HTTP/1.1 client with persistent connection reuse (keep-alive).
	transport := &http.Transport{
		ForceAttemptHTTP2:   false,
		TLSNextProto:        make(map[string]func(authority string, c *tls.Conn) http.RoundTripper),
		MaxIdleConns:        10,
		MaxIdleConnsPerHost: 10,
		IdleConnTimeout:     90 * time.Second,
		DisableCompression:  true, // Disable automatic gzip so wire size reflects raw JSON.
	}
	client := &http.Client{Transport: transport}
	defer transport.CloseIdleConnections()

	baseURL := fmt.Sprintf("http://%s/batch?size=", ln.Addr().String())

	if err := os.MkdirAll(filepath.Dir(*outPath), 0o755); err != nil {
		log.Fatalf("failed to create output dir: %v", err)
	}
	f, err := os.Create(*outPath)
	if err != nil {
		log.Fatalf("failed to create output CSV: %v", err)
	}
	defer f.Close()

	writer := csv.NewWriter(f)
	defer writer.Flush()

	if err := writer.Write([]string{
		"arquitetura",
		"payload_label",
		"payload_target_bytes",
		"item_count",
		"wire_bytes",
		"iteracao",
		"latencia_ms",
	}); err != nil {
		log.Fatalf("failed to write header: %v", err)
	}

	doRequest := func(label string) (int, float64, error) {
		start := clock.Now()
		resp, err := client.Get(baseURL + label)
		if err != nil {
			return 0, 0, err
		}
		body, err := io.ReadAll(resp.Body)
		resp.Body.Close()
		if err != nil {
			return 0, 0, err
		}
		if resp.StatusCode != http.StatusOK {
			return 0, 0, fmt.Errorf("unexpected HTTP status: %d", resp.StatusCode)
		}
		var decoded dataset.BatchResponse
		if err := json.Unmarshal(body, &decoded); err != nil {
			return 0, 0, err
		}
		elapsedMs := clock.SinceMs(start)
		if len(decoded.Items) != expectedCounts[label] {
			return 0, 0, fmt.Errorf("item count mismatch: got %d, want %d", len(decoded.Items), expectedCounts[label])
		}
		return len(body), elapsedMs, nil
	}

	for _, spec := range dataset.DefaultSpecs {
		runtime.GC()
		log.Printf("[REST] Warming up %s (%d requests)...", spec.Label, *warmup)
		for i := 0; i < *warmup; i++ {
			if _, _, err := doRequest(spec.Label); err != nil {
				log.Fatalf("warm-up failed on %s: %v", spec.Label, err)
			}
		}

		log.Printf("[REST] Measuring %s (%d requests)...", spec.Label, *iterations)
		var sumMs float64
		var lastWire int
		for i := 1; i <= *iterations; i++ {
			wireBytes, ms, err := doRequest(spec.Label)
			if err != nil {
				log.Fatalf("measurement failed on %s iter %d: %v", spec.Label, i, err)
			}
			sumMs += ms
			lastWire = wireBytes

			if err := writer.Write([]string{
				"REST",
				spec.Label,
				strconv.Itoa(spec.TargetBytes),
				strconv.Itoa(expectedCounts[spec.Label]),
				strconv.Itoa(wireBytes),
				strconv.Itoa(i),
				fmt.Sprintf("%.6f", ms),
			}); err != nil {
				log.Fatalf("failed to write row: %v", err)
			}
		}
		writer.Flush()
		log.Printf("[REST] Done %s | wire=%d bytes | mean=%.4f ms", spec.Label, lastWire, sumMs/float64(*iterations))
	}

	log.Printf("[REST] Benchmark completed. Results saved to %s", *outPath)
}
