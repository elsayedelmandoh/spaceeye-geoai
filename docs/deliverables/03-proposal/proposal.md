# SpaceEye GeoAI

**New Capital Radar: a company that owns a city.**

Supervisor: Dr. Nadim Abdin - Partner & VP Business Development
Team: Elsayed Elmandoh, Verina Fouad, Ahmed Abdelhameed, Nada Shady, Salma Magdy

## The problem

Eng. Khaled Abbas, chairman of ACUD, said in a public TV interview that there are about 500 real-estate developers and about 600 projects, and that no more than 7-8% of developers are late. He also said that field review happens every 3 months and that there were 6 mutual terminations.

A committee cannot visit everything every cycle, so the question is: which compounds first?

Our scope is R7: 12 coded compounds, a review every 3 months, and room for 4 visits per cycle.

## What SpaceEye does

- Reads public satellite data every quarter for each compound.
- A fixed rule (Track A) ranks the compounds from level 1 (inspect now) to level 4 (routine) and builds a cycle list of at most 4 compounds, each with a one-sentence reason.
- A dashboard shows the map, a file for each compound, and a chatbot that answers from project documents.
- The system recommends; the committee decides.

## Evidence and honest limits

- **Backtest:** on six public R7 cases the rule gave an early alert in 1 of 6 cases. The target of 5 was fixed before computing and was not met. In the five missed cases the sites were seen as active, so the rule had no stall to detect: it measures stalls and passed dates, not pace against plan.
- **Value:** under these assumptions, from 0.007 to 0.102 million EGP per year (illustrative; cost inputs are public proxies or assumptions). It is not a measured saving.
- **Generated data:** Track B (a trial model) uses only data marked "Synthetic - for training only". It shows nothing about real accuracy.
- Satellites show whether building is happening, not interior finishing. A level is not a finding against anyone.

## KPIs

| Indicator | What it measures | Unit | Role |
| --- | --- | --- | --- |
| A | Probability the compound is building this quarter | 0-1 | Input |
| K2 | Quarters with no activity after construction started | Quarters | Sets the level |
| K3 | Months since the first announced handover date | Months | Sets the level |
| K4 | Enough satellite images and a boundary to trust the signal | Yes/No | Gate |
| K5 | Months eligible for review under contract terms (screening exposure) | Months | Context only |
| K6 | Months since launch/promise with no confirmed start | Months | Sets the level |

The priority level is the worst of K2, K3 and K6 (plus one combined K2 and K3 rule), with no weights; the committee decides.

## Next step

**Decision requested:** use the priority list to choose which R7 compounds the committee visits first next cycle.

1. Run one pilot cycle with the list.
2. Record every visit result, to build real ground truth.
3. The current 3-month review keeps running, so going back costs at most one rerun.

People and dates are to be agreed with ACUD. This is what public data alone can do; with ACUD data the demo parts become real operation.

**Alignment with Egypt Vision 2030:** the knowledge and innovation goal (geographic AI that reads satellite images) and the governance goal (field inspections directed by data with a known source).
