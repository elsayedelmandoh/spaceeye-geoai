# Audience tests: what changed after review, and the ten-second test sheet

## Changed after review

Team members outside the dashboard role reviewed the screens as stand-ins for the committee (`logs/debate-03-dashboard.pdf`, `logs/debate-04-vital cards.pdf`). They are not committee members; a test with a real committee member is still needed (sheet below).

| What the reviewer saw | What changed | Where |
| --- | --- | --- |
| Text overflowing the indicator tiles (K3, K5, K6) | Tile values wrap inside the tile | PR #101 |
| Compound codes missing beside the bars in two charts | Every bar carries its code | PR #101 |
| C21 early-signal section read as incoherent | "No new building activity" instead of "no activity"; the reading carries its date | PR #101 |
| C21 "stalled 6 quarters" on one screen, "2" on another | Both are right at different dates (2020Q3 and 2026Q3); the date now sits next to each number | PR #101 |
| Rank shown for the first 4 only; tie rule and handover status unclear | Rank for every compound, tie rule stated, handover status shown, one line per scenario on what changes | PR #101 |
| Image pair missing because of the same-season rule | Any two capture dates, any season (owner decision) | PR #101 |
| Fine impact of 45 months not visible | K5 months in the decision card; fine exposure in EGP on Track B with the assumed rate labelled | PR #101 |
| Decision, chart and image on one screen without scrolling (split view) | Compound file shows decision card, tiles, latest capture and satellite curve in one view; the rest opens on demand | PR #102 |

Not taken up, because the numbers had no source: an "effort saved" percentage without a baseline and a cost matrix without sources. A rubric screen inside the dashboard was also left out.

## Ten-second test sheet (screen 1, Priority map)

For one person from the committee or the inspection team who has not seen the dashboard. Open screen 1 in Track A, show it for 10 seconds, close it, then ask the four questions. Write the answers word for word; do not help.

| # | Question | Answer from the current release (as of 2026Q3) |
| --- | --- | --- |
| 1 | Which compound should be visited first? | C18 |
| 2 | Why that one? | Its first announced handover date passed long ago (57 months) |
| 3 | How many compounds are on this cycle's list? | 4 (C18, C07, C14, C03) |
| 4 | Is any number on this screen made up? | No: Track A shows real and derived data only |

| Person (role, no name) | Date | Q1 | Q2 | Q3 | Q4 | Seconds to answer Q1 | What confused them |
| --- | --- | --- | --- | --- | --- | --- | --- |
| | | | | | | | |
| | | | | | | | |

Pass: Q1 and Q3 right without help. If someone fails, write what confused them, change the screen, and test a new person. Record the result here and in `docs/requirements/02-team-roles-and-tasks.md` (T-NA-08).
