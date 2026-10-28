# project timeline and milestones

Source: `docs/plan/project-plan.md` section 11. 6 working days are left: program days 6, 7, 8, 10, 11 and 12. Day 9 is the shift simulation, with no project work.

Roles: R1 data pipeline and quality · R2 real data and simulator · R3 GIS and satellite signals, then the complaint classifier · R4 analysis and agent · R5 dashboard and presentation.

> Calendar dates are still to be confirmed with the instructor. Fill the `date` column once they are fixed.

## overview

| plan day | program day | date | goal | done when |
| --- | --- | --- | --- | --- |
| D1 | day 6 | TBC | foundation and sign-off: compass canvas (8 checks), compound locations, **real tables**, config files | compass signed · at least 20 compounds located · `ingest` runs · both config files written · section 14 decisions signed |
| D2 | day 7 | TBC | first real priority list; simulator starts (**generated tables 1-5**) | first real cycle list with reason sentences |
| D3 | day 8 | TBC | evaluation: backtest; simulator complete (**generated tables 6-8**); `run_all.py` end to end | named backtest table · `run_all.py` builds everything |
| - | day 9 | TBC | shift simulation, no project work | - |
| D4 | day 10 | TBC | mid-review (10 min); track B, agent, **code freeze** | one command builds everything · dashboard + cycle list + 5 inspection files + decision memo |
| D5 | day 11 | TBC | delivery, knowledge transfer, 2 timed rehearsals, backup video | fixes only |
| D6 | day 12 | TBC | presentation to the ACUD panel | - |

## when the tables are built

| tables | owner | day |
| --- | --- | --- |
| `r_compounds`, `r_progress_announced`, `r_project_events`, `eval_outcomes`, `cfg_assumptions.yaml`, `cfg_scenarios.yaml` | R2 | D1 (day 6) |
| DuckDB with the real tables (`ingest.py`, first 4 gates) | R1 | D1 (day 6) |
| `locations_team.csv` (23 named compounds, ~5 per person) | everyone, 2 hours | D1 (day 6) |
| initial compound polygons (GeoJSON) | R3 | D1 (day 6) |
| `kpi_values`, `run_log` (K1-K4 and levels in SQL with `$asof`) | R1 | D2 (day 7) |
| simulator `simulate.py`, generated tables 1-5 + consistency checks | R2 | D2 (day 7) |
| Dynamic World + radar series, observed stage, Wayback images | R3 | D2 (day 7) |
| simulator generated tables 6-8 + all consistency checks | R2 | D3 (day 8) |
| final GeoJSON (second sign-off) | R3 | D3 (day 8) |
| `ops_visits` form | R5 | D3 (day 8) |
| data dictionary for every generated table | R2 | D4 (day 10) |

## daily tasks

### D1 (day 6): foundation and sign-off
| who | task | output |
| --- | --- | --- |
| everyone (2 h) | locate 23 named compounds (~5 each) on Google Maps or the developer's official map; known outcomes first (Venia, La Verde, Residence Eight, Park Lane, Anakaji, Scenario, Kardia, Moraya, Armonia, The Loft). broker sites not allowed | `locations_team.csv`: `project_id, lat, lon, method, url, confidence` |
| R1 | `app/` skeleton, `ingest.py`, first 4 gates, `run_all.py` skeleton | DuckDB with the real tables |
| R2 | `r_compounds`, `r_progress_announced`, `r_project_events` from confirmed records; `eval_outcomes`; `cfg_assumptions.yaml` and `cfg_scenarios.yaml` | tables + both config files |
| R3 | snap points to OSM plots; draw a polygon where no plot exists; area check (0.6-1.5) | initial GeoJSON |
| R4 | fix K1 (0.03) and K1b (0.5 dB) thresholds; independent radar review; section 6 experiment decisions in `decisions_log.md` | half-page memo |
| R5 | skeleton of the 4 screens | skeleton dashboard |

### D2 (day 7): first real list + simulator starts
| who | task | output |
| --- | --- | --- |
| R1 | K1-K4 and levels in SQL with `$asof`; `kpi_values`, `run_log` | KPI table |
| R2 | `simulate.py` tables 1-5 + consistency checks | half the simulator |
| R3 | Dynamic World (all classes) and radar for new polygons (scripts ready); observed stage; Wayback images | series + stages + images |
| R4 | cycle list at 2026-Q3 + reason sentence + test "every number in the sentence = its value" | first real list |
| R5 | screens 1 and 2 with real data | map + compound file |

### D3 (day 8): evaluation
| who | task | output |
| --- | --- | --- |
| R4 | backtest (2024-Q2, 2025-Q2) + sensitivity (with and without radar) | named table |
| R2 | `simulate.py` tables 6-8 + all consistency checks | full simulator |
| R1 | the 9 gates; `run_all.py` from raw to dashboard; two identical runs | one command works |
| R3 | polygon review with a second sign-off; final "not assessable" list; start masking in `complaints.py` | final GeoJSON |
| R5 | screens 3 and 4 + mode switch + `ops_visits` form | full dashboard skeleton |

### D4 (day 10): mid-review + track B, agent, freeze
Morning: mid-review (10 minutes): first cycle list + backtest + early dashboard + risks.

| who | task | output |
| --- | --- | --- |
| R4 | B1-B5 + compare the two rules (+ model if time allows); inspection-file agent + verification; 5 stored files; method card and monitoring plan | comparison + 5 files + verification log |
| R3 | complaint classifier vs keywords; governance cards for 3 datasets | result + 3 cards |
| R5 | final dashboard; decision memo (Arabic/English); EGP value slide | dashboard + memo |
| R2 | data dictionary for every generated table; ACUD data-request list; risks and responsible-AI note; wording audit | dictionary + list + note |
| R1 | **code freeze**; technical docs; run guide; knowledge-transfer draft | README + draft |

### D5 (day 11): delivery, knowledge transfer, rehearsal
Hand over all files · knowledge-transfer pack (quarterly rerun, owners, what may break, `cfg` files, `ops_visits` loop) · two timed rehearsals · backup video · 10-second test · cross-review (a source for every number, origin type visible, no "defaulted" label on a real compound) · **fixes only**.

### D6 (day 12): presentation to the ACUD panel
The live demo follows the dashboard routine: scan status, check freshness, compare, drill down, decide.
