package main

import (
	"context"
	"encoding/csv"
	"flag"
	"fmt"
	"log"
	"net"
	"os"
	"path/filepath"
	"runtime"
	"strconv"

	"grpc-x-rest/internal/clock"
	"grpc-x-rest/internal/dataset"
	"grpc-x-rest/proto/benchmarkpb"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/proto"
)

const maxMsgSize = 32 * 1024 * 1024 // 32 MB to comfortably support 4 MB+ payloads

type benchmarkServer struct {
	benchmarkpb.UnimplementedBenchmarkServiceServer
	batches map[string]*benchmarkpb.BatchResponse
}

func (s *benchmarkServer) GetBatch(_ context.Context, req *benchmarkpb.BatchRequest) (*benchmarkpb.BatchResponse, error) {
	batch, ok := s.batches[req.GetPayloadSize()]
	if !ok {
		return nil, status.Errorf(codes.InvalidArgument, "unknown payload size: %s", req.GetPayloadSize())
	}
	return batch, nil
}

func toProtoBatch(b dataset.BatchResponse) *benchmarkpb.BatchResponse {
	items := make([]*benchmarkpb.Item, len(b.Items))
	for i, it := range b.Items {
		items[i] = &benchmarkpb.Item{
			Id:          it.ID,
			Code:        it.Code,
			Name:        it.Name,
			Category:    it.Category,
			Description: it.Description,
			Price:       it.Price,
			Quantity:    it.Quantity,
			Active:      it.Active,
		}
	}
	return &benchmarkpb.BatchResponse{
		PayloadSize: b.PayloadSize,
		Items:       items,
	}
}

func main() {
	warmup := flag.Int("warmup", 100, "number of warm-up requests per payload size (discarded)")
	iterations := flag.Int("n", 1000, "number of measured requests per payload size")
	outPath := flag.String("out", filepath.Join("results", "raw_grpc.csv"), "output CSV file path")
	flag.Parse()

	// Pre-build identical domain batches in Protocol Buffers format.
	pbBatches := make(map[string]*benchmarkpb.BatchResponse, len(dataset.DefaultSpecs))
	expectedCounts := make(map[string]int, len(dataset.DefaultSpecs))
	wireSizes := make(map[string]int, len(dataset.DefaultSpecs))

	for _, spec := range dataset.DefaultSpecs {
		domainBatch, jsonBytes := dataset.BuildBatch(spec)
		pb := toProtoBatch(domainBatch)
		pbSize := proto.Size(pb)
		pbBatches[spec.Label] = pb
		expectedCounts[spec.Label] = len(domainBatch.Items)
		wireSizes[spec.Label] = pbSize
		log.Printf("[gRPC] Prepared payload %s: %d items, %d Protobuf bytes (vs %d JSON bytes)", spec.Label, len(domainBatch.Items), pbSize, jsonBytes)
	}

	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		log.Fatalf("listen failed: %v", err)
	}

	srv := grpc.NewServer(
		grpc.MaxRecvMsgSize(maxMsgSize),
		grpc.MaxSendMsgSize(maxMsgSize),
	)
	benchmarkpb.RegisterBenchmarkServiceServer(srv, &benchmarkServer{batches: pbBatches})

	go func() {
		if err := srv.Serve(ln); err != nil {
			log.Fatalf("gRPC server error: %v", err)
		}
	}()
	defer srv.Stop()

	conn, err := grpc.NewClient(
		ln.Addr().String(),
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithDefaultCallOptions(
			grpc.MaxCallRecvMsgSize(maxMsgSize),
			grpc.MaxCallSendMsgSize(maxMsgSize),
		),
	)
	if err != nil {
		log.Fatalf("gRPC dial failed: %v", err)
	}
	defer conn.Close()

	client := benchmarkpb.NewBenchmarkServiceClient(conn)

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
		ctx := context.Background()
		req := &benchmarkpb.BatchRequest{PayloadSize: label}
		start := clock.Now()
		resp, err := client.GetBatch(ctx, req)
		elapsedMs := clock.SinceMs(start)
		if err != nil {
			return 0, 0, err
		}
		if len(resp.GetItems()) != expectedCounts[label] {
			return 0, 0, fmt.Errorf("item count mismatch: got %d, want %d", len(resp.GetItems()), expectedCounts[label])
		}
		return wireSizes[label], elapsedMs, nil
	}

	for _, spec := range dataset.DefaultSpecs {
		runtime.GC()
		log.Printf("[gRPC] Warming up %s (%d requests)...", spec.Label, *warmup)
		for i := 0; i < *warmup; i++ {
			if _, _, err := doRequest(spec.Label); err != nil {
				log.Fatalf("warm-up failed on %s: %v", spec.Label, err)
			}
		}

		log.Printf("[gRPC] Measuring %s (%d requests)...", spec.Label, *iterations)
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
				"gRPC",
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
		log.Printf("[gRPC] Done %s | wire=%d bytes | mean=%.4f ms", spec.Label, lastWire, sumMs/float64(*iterations))
	}

	log.Printf("[gRPC] Benchmark completed. Results saved to %s", *outPath)
}
