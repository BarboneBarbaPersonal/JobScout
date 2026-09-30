package notify

import (
	"testing"

	"jobwatch/internal/model"
)

func TestRankByLocation(t *testing.T) {
	input := []Match{
		{Job: model.Job{Title: "a", Location: "Madrid, Spain"}},
		{Job: model.Job{Title: "b", Location: "Remote - Europe"}},
		{Job: model.Job{Title: "c", Location: "Lisbon"}},
		{Job: model.Job{Title: "d", Location: "Barcelona, Spain"}},
	}
	got := RankByLocation(input, []string{"barcelona", "remote", "spain"})

	want := []string{"d", "b", "a", "c"}
	for i, title := range want {
		if got[i].Job.Title != title {
			t.Fatalf("position %d: got %q, want %q", i, got[i].Job.Title, title)
		}
	}
	if input[0].Job.Title != "a" {
		t.Fatalf("input slice was modified")
	}
}
