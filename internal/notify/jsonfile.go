package notify

// JobScout: the "jsonfile" notifier appends every new match to a file, one
// JSON object per line. The workflow then merges that file into the job
// board web page (jobscout/build_page.py). No email, no network.
//
// Config:
//
//	- name: jsonfile
//	  params:
//	    path: new_matches.jsonl

import (
	"context"
	"encoding/json"
	"os"
	"time"

	"jobwatch/internal/params"
)

func init() {
	Register("jsonfile", func(p params.Map) (Notifier, error) {
		path, err := p.Require("path")
		if err != nil {
			return nil, err
		}
		return jsonFile{path: path}, nil
	})
}

type jsonFile struct{ path string }

func (jsonFile) Name() string { return "jsonfile" }

// jsonMatch is one line of the output file.
type jsonMatch struct {
	ID       string `json:"id"`
	Company  string `json:"company"`
	Title    string `json:"title"`
	Location string `json:"location"`
	URL      string `json:"url"`
	PostedAt string `json:"posted_at,omitempty"`
	FoundAt  string `json:"found_at"`
	// Description is the posting text, used by the CV analysis (jobscout-cv).
	// Capped so one huge posting cannot bloat the board's data file.
	Description string `json:"description,omitempty"`
}

const maxDescriptionChars = 15000

func (j jsonFile) Notify(_ context.Context, matches []Match) error {
	file, err := os.OpenFile(j.path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		return err
	}
	defer file.Close()

	now := time.Now().UTC().Format(time.RFC3339)
	encoder := json.NewEncoder(file)
	for _, m := range matches {
		line := jsonMatch{
			ID:       m.Job.ID,
			Company:  m.Job.Company,
			Title:    m.Job.Title,
			Location: m.Job.Location,
			URL:      m.Job.URL,
			FoundAt:  now,
		}
		line.Description = m.Job.Description
		if runes := []rune(line.Description); len(runes) > maxDescriptionChars {
			line.Description = string(runes[:maxDescriptionChars])
		}
		if !m.Job.PostedAt.IsZero() {
			line.PostedAt = m.Job.PostedAt.UTC().Format(time.RFC3339)
		}
		if err := encoder.Encode(line); err != nil {
			return err
		}
	}
	return nil
}
