package notify

// JobScout: order matches by where the job is, following a preference list
// such as ["barcelona", "remote", "spain"]. A job scores the position of the
// best (earliest) term found in its location, so "Barcelona, Spain" ranks as
// Barcelona. Jobs matching no term go last. Ties keep their original order.

import (
	"sort"
	"strings"
)

// RankByLocation returns a sorted copy of matches; the input is not changed.
func RankByLocation(matches []Match, preference []string) []Match {
	ranked := make([]Match, len(matches))
	copy(ranked, matches)
	score := func(m Match) int {
		location := strings.ToLower(m.Job.Location)
		for i, term := range preference {
			if strings.Contains(location, term) {
				return i
			}
		}
		return len(preference)
	}
	sort.SliceStable(ranked, func(a, b int) bool {
		return score(ranked[a]) < score(ranked[b])
	})
	return ranked
}
