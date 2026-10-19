// JobScout runner on freehire's crawling engine (github.com/strelov1/freehire, MIT).
//
// The scan copies this file into a freehire checkout (pinned in FREEHIRE_VERSION) as
// cmd/jobscout-scan and builds it there, because Go only lets code inside the freehire
// module use its internal packages.
//
// Input (stdin): [{"name": "Adyen", "link": "https://job-boards.greenhouse.io/adyen"}, ...]
// A company may also give "source" and "board" directly (e.g. {"source": "teamtailor",
// "board": "careers.paack.co"}) when JobScout already knows the board.
// Output (stdout), one JSON object per line:
//
//	{"kind": "job", ...}           one open job, with freehire's reading of its location
//	{"kind": "board", ...}         one crawled board: job count, time, error if any
//	{"kind": "unrecognized", ...}  a company whose link freehire can't map to a board
package main

import (
	"context"
	"encoding/json"
	"os"
	"sync"
	"time"

	"github.com/strelov1/freehire/internal/dict/location"
	"github.com/strelov1/freehire/internal/ingest/atsboard"
	"github.com/strelov1/freehire/internal/ingest/sources"
	"github.com/strelov1/freehire/internal/platform/htmltext"
)

const workers = 8                     // boards crawled at the same time
const boardTimeout = 25 * time.Minute // a stuck board must not block the whole scan

type company struct {
	Name   string `json:"name"`
	Link   string `json:"link"`
	Source string `json:"source"`
	Board  string `json:"board"`
}

type board struct {
	Company string   `json:"company"`
	Also    []string `json:"also"` // other sheet rows pointing at the same board
	Source  string   `json:"source"`
	Board   string   `json:"board"`
	Jobs    int      `json:"jobs"`
	Seconds float64  `json:"seconds"`
	Error   string   `json:"error,omitempty"`
	Kind    string   `json:"kind"`
}

type job struct {
	Kind        string     `json:"kind"`
	Company     string     `json:"company"`
	Source      string     `json:"source"`
	Board       string     `json:"board"`
	ExternalID  string     `json:"external_id"`
	URL         string     `json:"url"`
	Title       string     `json:"title"`
	Location    string     `json:"location"`
	PostedAt    *time.Time `json:"posted_at"`
	Description string     `json:"description"`
	WorkMode    string     `json:"work_mode"`
	Cities      []string   `json:"cities"`
	Countries   []string   `json:"countries"`
	Regions     []string   `json:"regions"`
}

func main() {
	var companies []company
	if err := json.NewDecoder(os.Stdin).Decode(&companies); err != nil {
		panic(err)
	}
	out := json.NewEncoder(os.Stdout)
	var mu sync.Mutex // one writer at a time on stdout
	emit := func(v any) { mu.Lock(); out.Encode(v); mu.Unlock() }

	// 1. Link -> board. Several sheet rows can point at one board (e.g. Loom -> Atlassian).
	boards := map[string]*board{}
	var order []string
	for _, c := range companies {
		source, slug, ok := c.Source, c.Board, c.Source != ""
		if !ok {
			source, slug, _, ok = atsboard.Recognize(c.Link)
		}
		if !ok {
			emit(map[string]string{"kind": "unrecognized", "company": c.Name, "link": c.Link})
			continue
		}
		key := source + "/" + slug
		if b, seen := boards[key]; seen {
			b.Also = append(b.Also, c.Name)
			continue
		}
		boards[key] = &board{Kind: "board", Company: c.Name, Source: source, Board: slug}
		order = append(order, key)
	}

	// 2. Crawl the boards, a few at a time.
	registry := sources.All(sources.NewClient())
	queue := make(chan *board)
	var wg sync.WaitGroup
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for b := range queue {
				crawl(registry, b, emit)
			}
		}()
	}
	for _, key := range order {
		queue <- boards[key]
	}
	close(queue)
	wg.Wait()
}

func crawl(registry map[string]sources.Source, b *board, emit func(any)) {
	start := time.Now()
	defer func() { b.Seconds = time.Since(start).Seconds(); emit(b) }()
	src, ok := registry[b.Source]
	if !ok {
		b.Error = "no adapter for " + b.Source
		return
	}
	ctx, cancel := context.WithTimeout(context.Background(), boardTimeout)
	defer cancel()
	jobs, err := src.Fetch(ctx, sources.CompanyEntry{Company: b.Company, Provider: b.Source, Board: b.Board})
	if err != nil {
		b.Error = err.Error()
	}
	b.Jobs = len(jobs)
	for _, j := range jobs {
		geo := location.Parse(j.Location)
		// Work mode: the platform's own field first, then the location text, then the
		// description ("hybrid, 3 days in the office"), as freehire's pipeline does.
		workMode := j.WorkMode
		if workMode == "" {
			workMode = geo.WorkMode
		}
		if workMode == "" {
			workMode = location.WorkModeFromDescription(j.Description)
		}
		emit(job{Kind: "job", Company: b.Company, Source: b.Source, Board: b.Board,
			ExternalID: j.ExternalID, URL: j.URL, Title: j.Title, Location: j.Location,
			PostedAt: j.PostedAt, Description: htmltext.ToText(j.Description), WorkMode: workMode,
			Cities: geo.Cities, Countries: geo.Countries, Regions: geo.Regions})
	}
}
