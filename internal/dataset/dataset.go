package dataset

import (
	"encoding/json"
	"fmt"
)

// PayloadSpec defines a benchmark payload target size.
type PayloadSpec struct {
	Label       string
	TargetBytes int
}

// DefaultSpecs defines the four payload sizes evaluated in the experiment:
// 1 KB, 100 KB, 1 MB, and 4 MB (covering the transition/inversion region
// highlighted in the systematic mapping study).
var DefaultSpecs = []PayloadSpec{
	{Label: "1KB", TargetBytes: 1 * 1024},
	{Label: "100KB", TargetBytes: 100 * 1024},
	{Label: "1MB", TargetBytes: 1024 * 1024},
	{Label: "4MB", TargetBytes: 4 * 1024 * 1024},
}

// Item represents a realistic structured domain entity exchanged between microservices.
type Item struct {
	ID          int64   `json:"id"`
	Code        string  `json:"code"`
	Name        string  `json:"name"`
	Category    string  `json:"category"`
	Description string  `json:"description"`
	Price       float64 `json:"price"`
	Quantity    int32   `json:"quantity"`
	Active      bool    `json:"active"`
}

// BatchResponse represents the REST JSON response payload.
type BatchResponse struct {
	PayloadSize string `json:"payload_size"`
	Items       []Item `json:"items"`
}

var categories = []string{
	"electronics",
	"infrastructure",
	"networking",
	"observability",
	"storage",
}

// makeItem builds a deterministic Item for a given index.
func makeItem(i int) Item {
	return Item{
		ID:          int64(i + 1),
		Code:        fmt.Sprintf("SKU-%07d", i+1),
		Name:        fmt.Sprintf("Microservice Benchmark Component %05d", i+1),
		Category:    categories[i%len(categories)],
		Description: fmt.Sprintf("Structured domain record %05d used to evaluate serialization and transport latency between REST and gRPC.", i+1),
		Price:       float64(1000+(i*37)%99000) / 100.0,
		Quantity:    int32(1 + (i*13)%500),
		Active:      i%2 == 0,
	}
}

// BuildBatch generates a deterministic BatchResponse whose JSON-serialized size
// is calibrated as closely as possible to spec.TargetBytes.
func BuildBatch(spec PayloadSpec) (BatchResponse, int) {
	// Measure a single representative item to estimate count.
	sample := BatchResponse{
		PayloadSize: spec.Label,
		Items:       []Item{makeItem(0)},
	}
	sampleBytes, _ := json.Marshal(sample)
	overhead := len(sampleBytes)
	if overhead <= 0 {
		overhead = 250
	}

	// Estimate item count and refine iteratively to match TargetBytes closely.
	count := spec.TargetBytes / overhead
	if count < 1 {
		count = 1
	}

	build := func(n int) (BatchResponse, int) {
		items := make([]Item, n)
		for i := 0; i < n; i++ {
			items[i] = makeItem(i)
		}
		resp := BatchResponse{
			PayloadSize: spec.Label,
			Items:       items,
		}
		raw, _ := json.Marshal(resp)
		return resp, len(raw)
	}

	resp, actual := build(count)
	// Linear adjustment using exact average bytes per item.
	if count > 0 {
		avgPerItem := float64(actual) / float64(count)
		refined := int(float64(spec.TargetBytes)/avgPerItem + 0.5)
		if refined < 1 {
			refined = 1
		}
		if refined != count {
			resp, actual = build(refined)
		}
	}

	return resp, actual
}
