# Governance: who decides, what can go wrong, when we review

Status: proposed by the team, not approved by ACUD. Roles are roles, not people; ACUD names the people. Data ownership and access per data group are in `docs/deliverables/governance-cards.md`; privacy and responsible use in `docs/deliverables/responsible-ai.md`.

## Who does what (RACI)

R = does the work, A = accountable (one per row), C = consulted, I = informed.

| Activity | Committee | Track A owner | Second reviewer | ACUD data custodian | Field visit lead | Track B / AI owner |
| --- | --- | --- | --- | --- | --- | --- |
| Quarterly run, quality gates, publish the list | I | A, R | R (reviews) | I | I | I |
| Review decision on every FLAG | I | A | R | C | | |
| Change a threshold, the capacity or the level order | A | R | C | C | C | I |
| Decide which compounds to visit and what follows | A, R | C | | | I | |
| Record every visit result | I | I | | | A, R | |
| Give or withdraw access to ACUD data; keep the code-to-name map | C | I | | A, R | | I |
| Keep generated data labelled and out of Track A | I | C | R | | | A, R |
| Turn on model calls in the chatbot (`configs/ai.yaml` `approval`) | C | C | R | C | | A |
| Merge to `main` (pull request with a recorded review) | I | A | R | | | R |

## Risk register

| Risk | Owner (role) | Early sign | Response |
| --- | --- | --- | --- |
| Activity score A fails on new quarters | Track A owner | Acceptance tests in `configs/data.yaml` (`activity`) fail | Set `source: k1` and state the narrower claim (`technical-track-a.md`) |
| The rule misses active-but-slow sites and finishing delays | Track A owner | 1 of 6 in the backtest (`data/BACKTEST_CURRENT.md`) | Say so on screen 3; a pace-against-promise indicator only after it is fixed and recorded before scoring |
| False alarms are unknown | Field visit lead | Visit results not recorded | Record all 12 visits in the pilot (`transition-plan.md`, gate A) |
| Generated data read as real | Track B / AI owner | Orange mark or banner missing | Separation gate (STOP), Track A by default, orange banner in Track B |
| A compound or developer name reaches the release | ACUD data custodian | `no_names` gate | Gate stops the run; names live only in `names/`, outside `data/` and the release |
| Developer claims run ahead of the structure | Track A owner | Claim far above what space shows (e.g. C19: 70% claimed, 28% of built area at 20 m or taller) | Show both side by side; the visit decides |
| Imagery missing or late | Track A owner | Freshness gate; K4 not assessable | Mark "not assessable"; a missing quarter never raises a level |
| Too many compounds for the list | Committee | More than 4 at level 1 or 2 (not seen in 31 quarters) | Raise capacity for that quarter or record who waits (`to-be.md`) |
| ACUD access not given or withdrawn | ACUD data custodian | No coded sample by gate A | Stay on public data; missing fields stay unknown |
| Fine wording read as an assessed fine | Track A owner | Text says "fine" without "eligible for review" | K5 is worded as months eligible for contract review; the contract decides (repo `CLAUDE.md`) |
| Model calls send data outside without approval | Track B / AI owner | `approval` changed without review | Off until approved; context holds codes only, no private mapping |

## Review schedule (proposed)

| When | What | Who |
| --- | --- | --- |
| Every quarter | Run, quality gates, FLAG decisions, the list; compare with the last accepted release | Track A owner, second reviewer |
| Every quarter, after visits | Visit results against the list: confirmed, false alarms, misses | Committee, field visit lead |
| Every two quarters | Thresholds, capacity and the activity acceptance tests, using the recorded visits; any change is a recorded decision | Committee, Track A owner |
| Every year | Access, retention and the roles in `governance-cards.md` | ACUD data custodian, committee |
| Every change to `main` | Pull request with an independent review and the test suite passing | Second reviewer |

## Decision log

| Date | Decision | Where it is recorded |
| --- | --- | --- |
| 2026-10-26 | Backtest success criterion fixed before any computation (5 cases; not lowered after the result) | `docs/requirements/01-specs.md` (success criterion), `data/BACKTEST_CURRENT.md` |
| 2026-10-29 | Level thresholds fixed before any score was seen, as stated by the person who set them (recorded 2026-10-28 in commit ca24988; git cannot prove the order) | `configs/data.yaml` (`levels`) |
| 2026-10-30 | Review round 03 decisions on the Track A run | `docs/deliverables/technical-track-a.md` (recorded decisions) |
| 2026-11-03 | Assumed rate for the Track B K5 screening exposure 1% to 0.5%, protocol frozen before the refit | `data/EW_PROTOCOL_RATE05.md` and its `.sha256` |
| 2026-11-03 | Image comparisons allowed across seasons (owner) | PR #101 |
| 2026-11-03 | Teammate dashboard review fixed and merged | PR #101 |
| 2026-11-03 | Failure modes, error costs, as-is, transition plan and one-view compound file merged after an independent review | PR #102 |
| 2026-11-04 | To-be targets and the problem chain merged after an independent review | PR #107 |

Add a row for every later decision; never edit an old row, add a new one that supersedes it.

## Open quality FLAG: 2019Q2 `data_or_city`

The gate flags a quarter when more than 30% of the compounds with a level show K2 = 1 at the same time (`src/pipeline/gates.py`, `g_data_or_city`). In 2019Q2 only one compound had a level (C03, K2 = 1), so the share is 1 of 1. With one compound the gate cannot tell a source event from one compound's stall, so the FLAG says nothing either way about the data.

Proposed review decision (pending the second reviewer's sign-off): accept as explained and keep it visible. Proposed for the next protocol, to be recorded before it is used and not applied now: run this gate only when at least 4 compounds have a level (2019Q1 to 2020Q2 had 1 or 2).
