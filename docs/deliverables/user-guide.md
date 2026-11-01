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

## Screen 1: Priority map and cycle list

Open **Screen 1 · Priority map** in the sidebar.

The map shows each coded project by its stored priority level. Hover over a project to see its code and priority word. The legend gives the count for each word. The caption gives the as-of quarter.

The cycle list is below the map. It shows the code, rank, priority level, Arabic reason, and available indicator columns. You can download the displayed list as a CSV.

The stored priority rule selects the cycle list. The dashboard reads the stored `cycle_rank`. If there is no stored rank, it selects levels 1 to 3 and orders them by level and code. A fitted probability does not select this list.

In Track B, the map stays hidden. A table of generated classifier results appears below the cycle list.

> Read aloud: “This map shows the stored priority of each coded project, and the list below shows the projects selected by the rule for this cycle.”

## Screen 2: Compound file and inspection file

Open **Screen 2 · Compound file** in the sidebar.

Use the **Compound** selector to choose a code. When a stored cycle rank is available, the first ranked code is selected by default.

The screen shows:

- the Arabic reason for the priority level;
- the priority level and the K2, K3, and K6 indicator tiles;
- context values, lineage, satellite curves, height and vegetation charts, and Wayback images when those stored files are available;
- the Track B generated indicators when Track B is active.

The screen reads the stored priority and indicators. It does not calculate a new priority while you use it.

### Inspection file button

The **Open inspection file** button provides the Arabic HTML report prepared for the selected code. The dashboard looks for:

`app_data/files/<code>_<quarter>.html`

If that exact quarter file is not there, it uses the latest matching `<code>_*.html` file for that code. If no report exists, the button is disabled and says it is not ready.

The report is local to the machine. The `app_data/` folder is git-ignored.

The dashboard caption says the report is drafted by AI from stored facts and reviewed before committee use. Inside the report, the AI paragraph appears only when it is present. It is labelled `Drafted by AI`. If there is no AI paragraph, the report says that it was prepared by code.

> Read aloud: “This file shows the stored evidence behind the priority for this code. I will open the prepared inspection report and review it with the other evidence.”

## Screen 3: Would it have warned?

Open **Screen 3 · Would it have warned?** in the sidebar.

In Track A, this screen reads the stored real public backtest cases. It uses the frozen clock. It shows:

- the stored backtest summary;
- one row per case, including the level reached and whether it warned early;
- the stored explanation for each case under **Why, case by case**, when present.

Read the definition of `early` and the frozen cutoff shown on the screen. The screen shows counts for the stored cases. It does not rerun the backtest live.

In Track B, this screen asks you to switch to Track A for the real-case backtest. It then shows generated model diagnostics and generated B1-B5 signals. These do not show real-world performance.

> Read aloud: “This screen tests the stored rule against public cases using a frozen clock. It gives context, not an automatic instruction for a current project.”

## Visit form

The visit form is at the bottom of Screen 2. Enter:

- **Code**: the project code, such as `C07`;
- **Date**: the visit date;
- **Result**: `progressing`, `stalled`, `complete`, or `not done`;
- **Note**: an optional note about what was seen.

The entries are saved to `app_data/ops_visits.csv`. This file is git-ignored and local to the machine.

The form appends each new entry. It does not overwrite earlier entries. If the file does not exist, the form creates it with a header. Saved visits are listed below the form, newest first.

A visit entry does not change the stored priority level.

> Read aloud: “After the visit, I will enter the code, date, result, and note. Saving adds a new row and keeps the earlier visit entries.”

## Screen 4: Data trust

This screen shows how far each number can be trusted: the quality gates, data coverage and the reviewed statements.

## Screen 5: What-if

This screen shows generated (Track B) what-if scenarios. S1 and S2 show Track B hypothetical levels and the cycle list against the baseline. S3 shows who is on the list at 2 or 6 visits instead of 4. Everything on it is marked Synthetic - for training only.

## If something looks wrong

1. Check the track switch first. Use Track A for real-data committee review.
2. On Screens 1 and 2, check the as-of quarter shown by the dashboard.
3. Look for a `Waiting for ...` message. It means a needed stored file is not present.
4. If the inspection file is not ready, check whether a report exists for the selected code.
5. Ask the dashboard owner about a screen or button problem. Ask the Track A data owner about missing or stale stored data. Ask the operations owner about a visit entry that did not save. Ask the AI component owner about the AI paragraph in an inspection report.
