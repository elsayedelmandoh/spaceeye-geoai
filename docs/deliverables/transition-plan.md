# Transition plan: from the fixed 3-month review to the priority list

Status: proposed by the team, not approved by ACUD. Owners are roles; ACUD names the people. Every number marked "proposed" is a starting point for the committee to change.

## In short

Three phases. During phases 1 and 2 the current practice (every R7 compound reviewed every 3 months) keeps running, so going back costs nothing: rollback means "stop reading the list". The list changes which compounds are visited first only after a committee decision at the gate into phase 3.

| Phase | Length (proposed) | Scope | What changes | Gate to the next phase |
| --- | --- | --- | --- | --- |
| 1 · Pilot cycle | 1 quarter | R7, 12 compounds | Nothing in the visit schedule. The committee reads the list (4 compounds) before the visits, and every visit result is recorded. | Gate A |
| 2 · ACUD data | 2 quarters | R7 | A first coded ACUD sample replaces assumptions; the list sets the visit order. All 12 are still visited. | Gate B |
| 3 · Quarterly operation | ongoing | R7, then R8 | The committee decides whether the list replaces part of the fixed schedule. R8 is added only after its own boundaries and statements pass the same gates. | Review every quarter |

## Phase 1: pilot cycle

- **List:** the current one (2026Q3): C18, C07, C14, C03 (capacity 4, `configs/data.yaml`).
- **Work:** visit as today. For every one of the 12 visits, record code, date and result (`progressing`, `stalled`, `complete`, `not done`) in the visit form on the Compound file screen (saved to `app_data/ops_visits.csv`). Recording all 12, not only the 4 listed, gives the first real count of false alarms and misses; the backtest cannot give one because all six of its cases were late.
- **Owners (roles):** the committee decides; the Track A owner prepares the list and checks the run; the field visit lead records results; a second team member reviews.
- **Resources:** no extra visits (the pilot uses visits already scheduled). One pipeline run on cached public data; one laptop. Refreshing imagery needs the original source workflow (`docs/deliverables/technical-track-a.md`).
- **Training:** one walk-through for committee users with `docs/deliverables/user-guide.md` (the screens, the Track A and B switch, what the levels mean); the field lead learns the visit form; the operator follows `docs/REVIEW_SETUP.md` and the quarterly procedure in `technical-track-a.md`.
- **Main risk:** too few cases to judge. Twelve visits are a go/no-go check, not an accuracy measurement; no accuracy claim is made from them.

## Phase 2: ACUD data

- **Work:** request the priority-1 rows of `docs/deliverables/data-request.md` (dated inspection and handover outcomes, contract register, parcel geometry), small verified sample first, codes only. Load, run the quality gates, compare against the public-data run. The list sets the order of the quarter's visits; all 12 are still visited and recorded.
- **Owners (roles):** ACUD data custodian (keeps the code-to-name mapping); Track A owner operates; second member reviews.
- **Main risk:** access or approval not given. Then phase 2 stays on public data and the gap is reported as unknown.

## Phase 3: quarterly operation

- **Work:** the quarterly monitoring procedure in `technical-track-a.md`. Thresholds and capacity change only through a reviewed, recorded decision. R8 enters only after its boundaries and statements are coded and pass the same gates; no transfer is claimed before that run.
- **Owners (roles):** the committee decides the visit policy; the Track A owner operates; a second member reviews each release.

## Gates (proposed criteria)

**Gate A, pilot to ACUD data.** All of:
1. Visit results recorded for 12 of 12 compounds in the pilot quarter.
2. The run had no STOP, and every FLAG has a written review decision.
3. The visit agrees with the listed reason for at least 2 of the 4 listed compounds.
4. No unlisted compound was found `stalled`. If one was, the committee reviews why before going on.
5. ACUD names a data custodian and approves the coded sample.

**Gate B, ACUD data to operation.** All of:
1. The ACUD sample loads with codes only (the `no_names` gate passes) and its dates are checked against publication dates.
2. Two consecutive quarterly runs without a STOP.
3. The activity score A passes its acceptance tests on the new quarters (`configs/data.yaml`, `activity`).
4. Visit results recorded for every visit in both quarters.
5. The committee records its decision on the visit policy in the decision log.

## Progress indicators (counted every quarter)

| Indicator | How it is counted | Source |
| --- | --- | --- |
| Visit results recorded | n of 12 compounds | `app_data/ops_visits.csv` |
| Listed compounds confirmed at the visit | n of 4 listed | visit results vs the list |
| Unlisted compounds found stalled (misses) | n of 8 unlisted | visit results vs the list |
| Days from list to visit | median over the quarter's visits | list date, visit dates |
| Run health | STOP count; FLAGs with a written decision, n of m | quality report |
| ACUD data received | n of 9 requested rows | `data-request.md` |

## Rollback

| Trigger | Action | Cost |
| --- | --- | --- |
| A run ends with a STOP | No new list that quarter; the last accepted release stays; visits follow the fixed schedule | none: the fixed schedule never stopped |
| A fails its acceptance tests on new quarters | Set `source: k1` under `activity:` in `configs/data.yaml` and state the narrower claim | one rerun |
| Gate A or B fails, or the committee rejects the list | Return to the fixed 3-month review; the list continues as a report only; record why | none |
| ACUD access withdrawn | Return to public data; missing fields stay unknown | one rerun |
| A name appears in a release | The `no_names` gate stops the run; nothing is published | none |

## What is not decided yet

People in each role, dates, the committee's own gate numbers, and whether the list will ever replace part of the fixed schedule. These need ACUD.
