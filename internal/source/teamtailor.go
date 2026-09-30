package source

// Teamtailor public RSS feed (no auth). Every Teamtailor career site,
// whether on {company}.teamtailor.com or a custom domain, serves:
//
//	GET https://{host}/jobs.rss
//
// Config:
//
//	- name: Sumsub
//	  source: teamtailor
//	  params:
//	    host: careers.sumsub.com    # the career site's host, no scheme

import (
	"context"
	"encoding/xml"
	"fmt"
	"net/http"
	"strings"
	"time"

	"jobwatch/internal/htmltext"
	"jobwatch/internal/model"
	"jobwatch/internal/params"
)

func init() {
	Register("teamtailor", func(company string, p params.Map, client *http.Client) (Source, error) {
		host, err := p.Require("host")
		if err != nil {
			return nil, err
		}
		return &teamtailor{company: company, host: strings.ToLower(strings.TrimSpace(host)), client: client}, nil
	})
}

type teamtailor struct {
	company string
	host    string
	client  *http.Client
}

func (t *teamtailor) Company() string { return t.company }

// teamtailorFeed mirrors the parts of jobs.rss we use. Location elements
// live in the tt: namespace; Go matches them by local name.
type teamtailorFeed struct {
	Items []struct {
		Title        string `xml:"title"`
		Description  string `xml:"description"` // HTML
		PubDate      string `xml:"pubDate"`
		Link         string `xml:"link"`
		RemoteStatus string `xml:"remoteStatus"` // "none", "hybrid", "fully"
		GUID         string `xml:"guid"`
		Locations    []struct {
			Name    string `xml:"name"`
			City    string `xml:"city"`
			Country string `xml:"country"`
		} `xml:"locations>location"`
	} `xml:"channel>item"`
}

func (t *teamtailor) Fetch(ctx context.Context) ([]model.Job, error) {
	url := fmt.Sprintf("https://%s/jobs.rss", t.host)
	body, err := fetchHTML(ctx, t.client, url, customListBodyLimit)
	if err != nil {
		return nil, err
	}
	var feed teamtailorFeed
	if err := xml.Unmarshal(body, &feed); err != nil {
		return nil, fmt.Errorf("teamtailor %s: parse rss: %w", t.host, err)
	}

	jobs := make([]model.Job, 0, len(feed.Items))
	for _, item := range feed.Items {
		// Build "Barcelona, Spain; Remote" style location text so
		// location keyword matchers see city, country and remote status.
		var places []string
		for _, loc := range item.Locations {
			parts := []string{}
			for _, part := range []string{loc.City, loc.Country, loc.Name} {
				if part = strings.TrimSpace(part); part != "" {
					parts = append(parts, part)
				}
			}
			if len(parts) > 0 {
				places = append(places, strings.Join(parts, ", "))
			}
		}
		switch item.RemoteStatus {
		case "fully":
			places = append(places, "Remote")
		case "hybrid":
			places = append(places, "Hybrid")
		}

		posted, _ := time.Parse(time.RFC1123Z, strings.TrimSpace(item.PubDate))
		jobs = append(jobs, model.Job{
			ID:          fmt.Sprintf("teamtailor/%s/%s", t.host, strings.TrimSpace(item.GUID)),
			Company:     t.company,
			Title:       strings.TrimSpace(item.Title),
			Location:    strings.Join(places, "; "),
			URL:         strings.TrimSpace(item.Link),
			Description: htmltext.ToText(item.Description),
			PostedAt:    posted,
		})
	}
	return jobs, nil
}
