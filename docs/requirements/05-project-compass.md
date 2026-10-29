> Program reference and unfinished project-signoff worksheet. Current technical decisions are in [D1_DECISIONS_CURRENT.md](D1_DECISIONS_CURRENT.md). This reference is not a signed SpaceEye compass; T-SA-01 remains pending.

# 07 | project compass

> Current technical decisions and unresolved approvals: [D1_DECISIONS_CURRENT](D1_DECISIONS_CURRENT.md). Implementation evidence: [partial-task closure](../../data/PARTIAL_TASKS_CLOSURE.md). Original checkboxes require the named reviewer and are not auto-signed.

graduation project · days 6-12 · for learners and instructors

synthetic data only - for training only.

## 1. the frame

at a strategic level, analytics can be reactive, preventive, or predictive. teams can apply one or more of these types to one or more of the eight pillars of a fourth-generation city, separately or in combination. the goal is to support city stability, sustainability, and citizen satisfaction in normal conditions and during extreme events such as crises.

your team chooses where to apply what you learned. choose one cell in the frame: an analytics type, one or more pillars, a condition, and the goal it serves.

| axis | choices |
| --- | --- |
| analytics type | reactive, preventive, or predictive |
| pillar(s) | one pillar, or two or more combined |
| condition | normal or extreme (crisis) |
| goal | stability, sustainability, or citizen satisfaction |

## 2. the three types of analytics

| type | what it does | key question | builds on |
| --- | --- | --- | --- |
| reactive | detects what happened and responds quickly | what happened, why, and what do we do now? | days 3-5 |
| preventive | watches for early warning signs and acts before a problem happens, using rules, thresholds, or leading indicators | what is about to happen, and what do we do now to stop it? | days 4-5 and 7 |
| predictive | estimates what will happen with a model whose accuracy is measured | how much, when, and where? | days 6-8 |

predictive analytics produces an estimate. preventive analytics produces a decision to act early; it may use a prediction or a rule. a project can combine both: a predictive forecast can trigger a preventive action.

## 3. the eight pillars

- mobility and traffic
- energy
- water
- waste
- public safety and surveillance
- buildings and facilities
- environment
- government and citizen services

combine pillars when a problem crosses them. for example, a dust storm affects environment, mobility, and public safety.

## 4. example angles

these examples are conversation starters, not a list to choose from. two teams may choose the same cell if their ideas differ.

| angle | nearest type | condition | example question |
| --- | --- | --- | --- |
| crisis discovery and management | reactive to preventive | extreme | how quickly can we distinguish a real incident from a data fault, and who should we alert? |
| simulation (what if?) | preventive | both | if a heatwave lasts five days, which buildings breach comfort limits first? |
| predictability | predictive | both | how many requests will each zone receive next week? |
| optimisation | preventive or predictive | normal | which collection route order empties the fullest bins first? |
| data trust and observability | reactive to preventive | normal | which feeds are drifting or late before a kpi goes wrong? |
| genai operator copilot | reactive | extreme | can an assistant draft a shift handover where every number is traceable? |
| spatial intelligence and equity | reactive or preventive | normal | which zones get slower service per resident, and why? |

## 5. teams

- 25 learners form teams of 4 to 6: five teams of 5, or six teams (five teams of 4 and one team of 5). the instructor confirms teams on day 6.
- each team includes mixed roles: analytics engineer and data science engineer.

## 6. your data

all teams work in the same oasis district. you may use the kit and extend it with your own synthetic data, such as a new table, scenario, or longer period.

rules for your synthetic data:

1. generate it in code with a fixed random seed so anyone can recreate it.
2. provide a data dictionary for every new table, including column, type, unit, range, and meaning.
3. use plausible values linked to the kit's zones, dates, and ids.
4. include at least one planted story and its answer key to show that your method can find it.
5. do not use real people, real idea data, or names of real systems. every file must say "synthetic - for training only".

## 7. is your idea ready? (day 6 sign-off)

the instructor signs off when the use-case canvas answers all eight checks:

1. **the cell:** analytics type × pillar(s) × condition.
2. **the goal:** stability, sustainability, or citizen satisfaction, and why.
3. **the decision:** what decision the project supports and its owner (a role).
4. **one kpi card:** baseline, target, and thresholds, using the day 4 format.
5. **a measurable success criterion.**
6. **the data plan:** kit tables plus your own synthetic tables (see section 6).
7. **a risk and responsible-ai note:** privacy, fairness, and misuse.
8. **feasibility:** achievable in the project sessions (days 6-11).

## 8. what each team delivers (day 12)

1. an indicator framework with kpi cards and a kpi tree.
2. a pipeline that computes the kpis and runs quality checks.
3. an analytical core that matches your chosen type:
   - **reactive:** detection and root-cause analysis, supported by evidence.
   - **preventive:** an early-warning rule, threshold, or simulation tested on past data.
   - **predictive:** a model with a baseline and measured error.
4. an operational dashboard.
5. a model card or method card, plus a monitoring plan.
6. a risk and responsible-ai check, plus an ai verification log.
7. technical documentation, a user guide, and a knowledge-transfer pack.
8. a bilingual decision brief and the final presentation.

## 9. timeline

| day | milestone |
| --- | --- |
| day 6 | kickoff: form teams, review the frame, choose a cell, complete the use-case canvas, and get sign-off |
| days 7-8 | complete the data plan and produce the first kpi and analytical result |
| day 9 | shift simulation; no project work |
| day 10 | sprint and mid-project review; 10 minutes per team |
| day 11 | delivery and knowledge transfer |
| day 12 | presentations to the idea evaluation panel |

---

## company context

ACUD (Administrative Capital for Urban Development, ACUD) is shaping the future of Egypt — planning, developing, and transforming Egypt's New Capital into a global hub for innovation, sustainability, and investment.

- Program: 12-day graduation structure: Week 1 (city & data), Week 2 (indicators + models + operations), Day 12 (panel pitch + rubric scoring).
- Ecosystem: IoT sensors, FTTx, data centers, smart utilities (energy/water/cooling), traffic, waste, citizen services (`service_requests`).
- Dataset: `ACUD_Oasis` synthetic district (6 zones, ~60,000 residents) — traffic, energy, water, waste, citizen complaints. Not ACUD operational data; synthetic for training only.
- Governance: Egyptian Personal Data Protection Law No. 151/2020, PII masking before/after verification, least-privilege role access, 6-dimension quality audit (completeness, validity, accuracy, consistency, timeliness, uniqueness), Data Trust Score per output.
