# Committee user guide (T-NA-10)

## Before you start

The dashboard reads stored files. It does not run the data build or fit a model live.

Use Track A for committee review. It is the default track. It shows real public observations and values derived from them.

Use project codes, such as `C07` or `D03`. Do not use a compound name or a developer name.

## Track switch and origin marks

The track switch is in the sidebar.

- **Track A** uses stored real public data and derived values. It is the default.
- **Track B** adds generated numbers. It shows the orange banner `Synthetic - for training only`. The priority map is hidden in this track. Track B is for training only.

The dashboard uses these origin marks:

- 🟢 **Real**: published as observed.
- 🔵 **Derived**: calculated from real data.
- 🟠 **Generated**: made for training.

Generated numbers carry the orange generated mark. Generated table headings also carry the mark. Do not treat generated numbers as observations.

## Priority levels

The dashboard shows these priority levels and words:

| Priority level | Dashboard word |
| --- | --- |
| 1 | Inspect now |
| 2 | Inspect this cycle |
| 3 | Document review |
| 4 | Routine |
| Grey | Not assessable |

These are visit priorities. They are not findings about a project. Grey means `Not assessable`; it is not an extra priority level.

## Screen 1: Priority map

Open **1 · Priority map** in the sidebar. The headline names the compounds to visit this cycle and why the first one comes first.

The screen shows, from top to bottom:

- **Summary tiles**: compounds to visit this cycle, compounds at level 1, fine-eligible months and in how many compounds, and promised handover dates still ahead.
- **This cycle's visits**: one card per compound with its latest Wayback capture, level and reason.
- **Priority map**: every coded compound coloured by level; block height is the mean building height. Right-drag to tilt or turn. The map is hidden in Track B.
- **Visit list**: rank, code, level, a suggested action and the reason. Download it as a CSV.
- **Changes since the previous quarter**: compounds that joined or left the visit list, with their level before and now.
- **Promised dates ahead**: the developers' confirmed promised dates that have not passed yet, soonest first.

The stored rule selects the visit list (`cycle_rank`). Suggested actions (monitor, document review, visit, written warning, fine review, confirm handover on site) are proposals built from the stored levels and clocks with named thresholds; the committee decides.

> Read aloud: "These are the compounds the rule puts first this cycle, and the action we suggest for each. The committee decides."

## Screen 2: Compound file

Open **2 · Compound file** and choose a code. The first compound on the visit list is selected by default.

The screen shows:

- the level, the suggested action and the last recorded visit;
- the reason for the level and the K2, K3, K6 and K5 tiles. K5 is a count of fine-eligible months; the contract decides any fine. When a handover date has passed but the compound may be complete, K3 says "date passed, may be handed over: confirm on site" instead of 0;
- the level history since 2019 and the satellite activity curves;
- the construction stage by year;
- the Wayback timeline: pick a capture date to see it large, or compare two dates side by side;
- the developer's published claims (progress and promised dates) beside the nearest capture and the construction stage in the promised year;
- the visit form.

### Inspection file

In Track B the screen offers the Arabic inspection file for this quarter (`app_data/files/<code>_<quarter>_inspection.html`). The files include generated figures (simulated complaints), so Track A does not offer them.

## Screen 3: District view

Open **3 · District view**. It shows what the system adds across R7:

- **An early signal**: the public late case flagged earliest after construction started (C21), what space showed then, its level at the freeze date and what happened later. It is one case, not a success rate.
- **Flagged now, before any handover date passed**: compounds on the list whose first date has not passed.
- **The developer said, space saw**: one compound's claims against its captures.
- **Homes in compounds with fine-eligible months**: published unit counts only.
- **How late R7 handovers ran**: months between the promised date and the first handover for the public cases.
- **Fine-eligible months** by compound, **developers with several compounds**, and the **level history** of all compounds.

## Screen 4: Scenarios

Open **4 · Scenarios** in Track B. Everything on it is generated and marked Synthetic - for training only. S1 raises imported costs by 30%, S2 lowers collections by 25% for six months, S3 changes the number of visits per cycle to 2 or 6. When nobody changes level or list, the screen says so in one line.

## Visit form

The visit form is at the bottom of Screen 2. Pick the **Code** from the list, then enter the **Date**, the **Result** (`progressing`, `stalled`, `complete`, or `not done`) and an optional **Note**.

The entries are saved to `app_data/ops_visits.csv` (git-ignored, local to the machine). Each save adds a row; earlier rows are kept. Saved visits are listed below the form, newest first, and the latest one shows in the compound file header. A visit entry does not change the stored priority level.

> Read aloud: "After the visit, I will enter the code, date, result, and note. Saving adds a new row and keeps the earlier visit entries."

## If something looks wrong

1. Check the track switch first. Use Track A for real-data committee review.
2. On Screens 1 to 3, check the as-of quarter shown by the dashboard.
3. Look for a `Waiting for ...` message. It means a needed stored file is not present.
4. If the inspection file is missing, switch to Track B and check whether a file exists for the selected code and quarter.
5. Ask the dashboard owner about a screen or button problem. Ask the Track A data owner about missing or stale stored data. Ask the operations owner about a visit entry that did not save. Ask the AI component owner about the AI paragraph in an inspection report.
