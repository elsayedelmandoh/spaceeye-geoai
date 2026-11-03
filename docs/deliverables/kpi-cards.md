# KPI cards

Task T-SA-02. Roles below are proposed operational responsibilities. No institutional approval or named-member sign-off is asserted. Numeric definitions match [`configs/kpis.yaml`](../../configs/kpis.yaml); thresholds are sourced from `configs/data.yaml`. Specification: [01-specs.md](../requirements/01-specs.md).

**Scope:** R7 only, 12 coded compounds, reporting quarter 2026Q3. Codes only, no names.

**Origin key:** 🟢 real · 🔵 derived · 🟠 generated (Track B only, "Synthetic - for training only").

**Tags:** tags from the program format table in 01-specs.md; reviewer to confirm (kpi_reference.csv is not in the repo).

## Card A: Activity score

| Field              | Value                         |
| ------------------ | ----------------------------- |
| Purpose            | Is it building?               |
| Unit               | Probability 0-1               |
| Source             | Dynamic World + Sentinel-2    |
| Frequency          | Quarterly                     |
| Owner (role)       | Spatial data analyst          |
| Baseline           | K1 (DW change alone)          |
| Target             | Set by owner                  |
| Thresholds         | Model threshold (out-of-fold) |
| Leading/lagging    | Leading                       |
| International axis | Urban planning                |
| Origin             | 🔵 derived                    |
| Tags               | Leading; Urban planning       |

A is the probability that the compound is building this quarter. It does not measure completion or finishing.

## Card K2: Quarters with no activity

| Field              | Value                                                             |
| ------------------ | ----------------------------------------------------------------- |
| Purpose            | For how long has it not been?                                     |
| Unit               | Quarters                                                          |
| Source             | A                                                                 |
| Frequency          | Quarterly                                                         |
| Owner (role)       | Spatial data analyst                                              |
| Baseline           | 0                                                                 |
| Target             | 0-1 (copied from the specification; meaning pending confirmation) |
| Thresholds         | 2 / 4                                                             |
| Leading/lagging    | Leading                                                           |
| International axis | Urban planning                                                    |
| Origin             | 🔵 derived                                                        |
| Tags               | Leading; Urban planning                                         |

K2 counts consecutive latest quarters with A below its threshold, **only after construction started**. A compound counts as started after 4 active quarters in a row, or once a launch or delivery event is published. K2 ≥ 4 gives level 1, K2 = 2-3 gives level 2, K2 = 1 gives level 3. Unknown never raises a level.

## Card K3: Handover clock

| Field              | Value                               |
| ------------------ | ----------------------------------- |
| Purpose            | Has it passed its first commitment? |
| Unit               | Months                              |
| Source             | Statements + Decree 2184            |
| Frequency          | Per statement / quarter             |
| Owner (role)       | Developer follow-up officer         |
| Baseline           | First announced date                |
| Target             | <= 0                                |
| Thresholds         | 12 / 24                             |
| Leading/lagging    | Lagging                             |
| International axis | Housing                             |
| Origin             | 🟢 real                             |
| Tags               | Lagging; Housing                     |

K3 is measured from the **first** announced handover date. Later promises never move that start date; K3 is 0 once a handover is published. It uses the nearest month (days / 30.44). K3 > 24 gives level 1, K3 = 13-24 gives level 2, K3 = 1-12 gives level 3. The developer announced the date; it is not an independent measurement.
The data table also holds display-only assumed dates (marked "assumption", with their basis) that fill missing schedule dates. They never replace a published date and never set a level.

## Card K4: Assessability

| Field              | Value                    |
| ------------------ | ------------------------ |
| Purpose            | Can we trust the signal? |
| Unit               | Yes/No                   |
| Source             | DW + boundaries          |
| Frequency          | Quarterly                |
| Owner (role)       | Data engineer            |
| Baseline           | -                        |
| Target             | 100%                     |
| Thresholds         | >= 6 images              |
| Leading/lagging    | Guard                    |
| International axis | Governance/data          |
| Origin             | 🟢 real                  |
| Tags               | Guard; Governance/data  |

K4 needs at least 6 Dynamic World images in the quarter plus a boundary with a reviewed confidence label. No numeric confidence threshold is defined. If K4 fails, the result is **Not assessable** and no level is assigned.

## Card K5: Contract review eligibility (policy screening months)

| Field              | Value                                    |
| ------------------ | ---------------------------------------- |
| Purpose            | How long has it been eligible for review under contract terms? |
| Unit               | Months (real); EGP (generated only)      |
| Source             | K3, K6 + contract fine rate (assumed)    |
| Frequency          | Quarterly                                |
| Owner (role)       | Developer follow-up officer              |
| Baseline           | 0                                        |
| Target             | 0                                        |
| Thresholds         | Context, no level                        |
| Leading/lagging    | Lagging                                  |
| International axis | Governance/data                          |
| Origin             | 🔵 derived (months) / 🟠 generated (EGP) |
| Tags               | Lagging; Governance/data                  |

K5 is illustrative policy screening, **not an assessed legal fine**. It never sets a priority level. K5 uses calendar months. Illustrative assumptions (from `configs/data.yaml`, `assumption: true`): monthly rate 1% of assumed land value, land price EGP 2,500-12,000 per m², allocation lag 6-18 months. EGP amounts exist only on generated data (Track B) and are not actual fines or verified losses.
Compounds without a published delivery date show an empty K5 with a stated reason; a separate display-only assumed K5 (marked "assumption") may be shown beside it. It is never a real K5 value and never sets a level.

## Card K6: No-construction-start clock

| Field              | Value                          |
| ------------------ | ------------------------------ |
| Purpose            | Is land held without building? |
| Unit               | Months                         |
| Source             | A + statements                 |
| Frequency          | Quarterly                      |
| Owner (role)       | Spatial data analyst           |
| Baseline           | First launch / promise date    |
| Target             | 0 (started)                    |
| Thresholds         | 13-24 / > 24                   |
| Leading/lagging    | Leading                        |
| International axis | Urban planning                 |
| Origin             | 🔵 derived                     |
| Tags               | Leading; Urban planning        |

K6 counts months without a **confirmed observed start**, measured from the first published launch or promise. It is not proof that no construction took place. If any quarter since the launch/promise is not assessable, K6 is unknown, and unknown never raises a level. K6 > 24 gives level 1, K6 = 13-24 gives level 2.
The table also has a K6 status column: it says whether K6 has a value, does not apply because construction was observed to start, or is unknown because satellite observation was interrupted.

## KPI tree

| Level       | Indicators                                                       | Owner (role)                       |
| ----------- | ---------------------------------------------------------------- | ---------------------------------- |
| Strategic   | Reliable handover in R7                                          | Buildings & Facilities pillar lead |
| Tactical    | Share of compounds in level 1-2, K3 overruns, K5 months eligible for review under contract terms | Head of the inspection committee   |
| Operational | A, K2, K6, K4 (guard), share of cycle-list visits done           | Observatory team                   |

## Priority levels

The priority level is the **worst** applicable level among K2, K3 and K6, with no weights. K2 counts only after construction started (4 active quarters in a row, or a published launch or delivery event). The "may be complete" cap (below) then limits the level to 3. The term is "priority level" (whom to visit first), never "risk level".

| Level                | Condition                                                 | Action                                            |
| -------------------- | --------------------------------------------------------- | ------------------------------------------------- |
| 1 Inspect now        | K2 >= 4, or K3 > 24, or (K2 >= 2 and K3 > 12), or K6 > 24 | Visit within two weeks and inform the pillar lead |
| 2 Inspect this cycle | K2 = 2-3, or K3 = 13-24, or K6 = 13-24                    | Within the cycle's visits                         |
| 3 Document review    | K2 = 1, or K3 = 1-12                                      | Request the supervisor report                     |
| 4 Routine            | Otherwise, when construction has started                  | Next cycle                                        |

## Follow-up states (no priority level)

These are lifecycle states, not priority levels.

| State          | Condition                                                                   | Action                     |
| -------------- | --------------------------------------------------------------------------- | -------------------------- |
| Not started    | No construction start, K6 known and <= 12 months, no K3 deadline has passed | Watch                      |
| Start unknown  | No construction start and K6 unknown                                        | Watch and collect evidence |
| Not assessable | K4 failed                                                                   | Fix location/images first  |

Unknown values never raise a level.

## "May be complete" cap

If a handover is announced, or vegetation share is >= 0.10, the level is capped at 3 and the flag **May be complete - confirm on site** is added. In 2026Q3 the cap sets 3 of the 12 levels: C03 and C12 (K2 = 6) and C21 (K2 = 2), all at level 3. This is a flag for on-site confirmation, not proof of completion and not a completion prediction.

## Cycle selection

Capacity is 4 compounds. Only levels 1-3 are eligible. Order: level ascending, then K2 descending, then K3 descending, then code ascending.

## Track B (generated, diagnostic only)

Track B uses generated data only and is labelled "Synthetic - for training only". Signals B1-B5 come from generated ACUD-style tables.

- B1 together with K2 >= 2 gives level 1.
- Any of B1, B2, B3, B5 gives at least level 2.
- B4 is context only.

Generated signals are never used to label a real Track A compound as distressed. The Track B model is binary (distressed / not_distressed in the next six months) and does not predict completion. Operational cycle selection uses the rule.

## Evidence requirements

Every number carries an origin mark. Developer statements are real but not independent measurements, so we write "the developer announced". Reason sentences use codes only.

## Backtest

Six R7 public cases, source: [BACKTEST_CURRENT.md](../../data/BACKTEST_CURRENT.md).

- After-start reading: **1 of 6**.
- Point-in-time reading: **0 of 6**.
- The original criterion (5 cases, fixed before computation) was not reduced and was **not achieved**.

For the numeric alternative check, the six cases had 3-12 assessable quarters before the frozen cutoff (10, 9, 12, 6, 10 and 3; the cases span 14-22 quarters in total before it), which rejects "too few images" as the explanation. This does not rule out coverage effects within those quarters. Warning detection is not causal proof. Counts only, no percentages.

## Limitations

- Satellites show whether building is happening, not interior finishing, so no completion % or finishing % is given.
- K3 relies on developer statements.
- K5 is illustrative and never a fine.
- Track B results are on generated data and do not show real-world accuracy.
- Two tags per card are pending (`kpi_reference.csv` is not in the repository).
