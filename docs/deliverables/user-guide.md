# Committee user guide (T-NA-10)

This guide describes the four sidebar screens of the dashboard, the visit list on screen 1 and the visit form on screen 2. Each section lists the screen content and the committee-facing wording required for each label. Labels in the dashboard must use this wording. Each section ends with an implementation note that names the functions it traces to.

The browser was not run for this guide. The implementation notes were checked against the code, and the required committee-facing wording is stated explicitly.

The dashboard reads stored files. It does not run the data build or fit a model live.

Use project codes such as `C07` or `D03`. Do not write a compound or developer name in a note or a visit entry.

*Implementation note:* `load_table`, `enforce_no_names`, `CODE_PATTERN` (app.py).

## Track switch and origin marks

The track switch is the **Track** box in the sidebar. The two options are `Track A: images` (the default) and `Track B: images + numbers (generated)`. The help text reads "Track A: public/derived data. Track B: adds generated ACUD-style data."

- **Track A** shows stored real observations and values derived from them. Stored generated tables are refused in this track.
- **Track B** shows the orange banner `Synthetic - for training only` on every screen. It also adds the generated items marked below. The sidebar caption reads "Generated numbers tagged · map hidden".

The sidebar pill in Track A reads `🟢 REAL · 🔵 DERIVED`. In Track B it reads `🟠 GENERATED`.

Origin marks used on the screens:

- 🟢 **Real**: named in the Track A sidebar pill.
- 🔵 **Derived**: on the metric tiles, the priority map caption and the satellite curves caption.
- 🟠 **Generated**: on the inspection file buttons, on the scenario and progress captions in screen 4, and on the Track B sidebar pill.

The district view does not use the track switch. The visit list changes only by the Track B inspection file buttons described in screen 1.

*Implementation note:* `TRACKS`, `TRACK_A`, `TRACK_B`, `render_sidebar`, `render_banner`, `load_table`, `ORIGIN_REAL`, `ORIGIN_DERIVED`, `ORIGIN_GENERATED`, `metric_tile`.

## Priority words

The stored level is shown with one of these words, from `level_word`.

| Level | Word on screen |
| --- | --- |
| 1 | Inspect now |
| 2 | Inspect this cycle |
| 3 | Document review |
| 4 | Routine |
| not assessable | Not assessable (grey) |

The stored rule selects the visit list, using `cycle_rank`. The suggested action on the cards, the visit list and the compound header is a proposal, and the committee decides. The table lists the suggested actions in the order the code checks them.

| Suggested action | When it is shown |
| --- | --- |
| No action | Level not assessable this quarter. |
| Fine review | Level 1 or 2, and K5 is at least 12 months eligible for review under contract terms. |
| Confirm handover on site | Level 3 and the compound may be complete. |
| Monitor | Level 4 and the compound may be complete. |
| Written warning | K3 is at least 12 months past the first announced date, or K2 is at least 4 quarters without activity. |
| Monitor | Level 4 (routine). |
| Document review | Level 3. |
| Visit this cycle | Level 2. |
| Visit now | Level 1. |

The 12-month and 4-quarter thresholds are named proposals in the code. Each suggested action shows its threshold next to its reason. "Fine review" and "Written warning" are workflow prompts only: they do not assert an assessed fine, an issued warning or any sanction, and the committee decides the action.

*Implementation note:* `LEVELS`, `NOT_ASSESSABLE`, `level_word`, `build_cycle_list`, `insights.suggested_action`, `insights.WARNING_K3_MONTHS`, `insights.WARNING_K2_QUARTERS`, `insights.FINE_REVIEW_K5_MONTHS`.

## Screen 1: Priority map

Open **1 · Priority map**. The subtitle reads "Whom should the committee visit first?". The screen shows these parts, in this order. If the KPI file is missing, the screen shows "Waiting for real/kpi_values.parquet." under the visit list heading.

1. **Headline.** One sentence, shown when the KPI file loads. It names the compounds on the visit list for this cycle, the count of compounds, the first compound and the reason for it. If compounds at levels 1 to 3 are waiting for the next cycle, it adds how many. If the list is empty, it says that no compound needs a visit this cycle.
2. **Summary tiles.** Four tiles, each with the derived mark and an "as of" caption:
   - **To visit this cycle**: the number of compounds on the list, with the caption "of N".
   - **At level 1**: the number of compounds at level 1, with the caption "inspect now".
   - **Months eligible for review under contract terms**: the total of K5 over compounds with a value above zero, with the caption "in K compounds · the committee decides any action".
   - **Promised dates ahead**: the number of confirmed promised dates not yet passed, with the caption "in K compounds".
3. **This cycle's visits.** One card per compound on the list. Each card shows the rank and code, the level word as a coloured pill and the short stored reason. If a Wayback capture exists, the card shows the latest capture and the caption "Wayback capture" with its date.
4. **Priority map** (Track A only). A block map of the coded compounds, coloured by level word. The legend gives the count for each word, including Not assessable. Block height is the mean building height in the latest year to 2024, drawn 10 times taller. A compound with no height on file is drawn flat, and its tooltip reads "no height on file". The caption reads "colour = priority level, grey = not assessable" and "right-drag to tilt or turn". In Track B the heading and the map are not drawn.
5. **Visit list.** The caption "Suggested actions are proposals; the committee decides." is followed by a table with the columns Rank, Compound, Level, Suggested action and Why, in visit order. A button labelled "⬇️ Cycle list (CSV)" saves the list as `cycle_list_<quarter>.csv`. In Track B, each compound with a stored inspection file also gets a button labelled "🟠 CODE inspection file (includes generated figures)". If the CSV check fails, the screen shows the error in place of the button.
6. **Changes since the previous quarter.** The heading reads "Changes since <quarter>". Two boxes, "Joined the list" and "Left the list", each show "No change." or one line per compound: the code, the move in the form "level 2 to 1" (or "none"), and the stored reason. This part appears only when a previous quarter exists in the KPI file.
7. **Promised dates ahead.** The heading reads "Promised dates ahead". The table has the columns Compound, Promise, Said in and Due by, sorted by due date. The caption reads "A visit before these dates can check the developer's own promise." If none is ahead, the screen says "No promised date is still ahead."

*Implementation note:* `screen_priority_map`, `cycle_headline`, `render_summary_tiles`, `render_cycle_cards`, `render_map_slot`, `render_visit_list`, `visit_table`, `render_changes`, `_level_move`, `render_promises_ahead`, `load_promises_ahead`, `insights.upcoming_promises`, `export_csv`.

## Screen 2: Compound file

Open **2 · Compound file**. The subtitle reads "Why this one? Evidence behind the priority level." The **Compound** box lists each code with its level word, for example "C07 · Inspect now". The first compound on the visit list is selected by default. If a compound has no KPI row for the quarter, the screen shows "CODE has no KPI row for <quarter>: shown as not assessable."

The decision, the indicators, the latest image and the satellite curve fit in one view; the rest of the evidence opens on demand. The screen shows these parts, in this order.

1. **Header.** Beside the **Compound** box, a card in the form "Level N · word. Suggested action: X. <reason>. Last recorded visit: <date> (<result>)." followed by "Why:" and the stored reason. If no visit is recorded, it says "no visit recorded yet". The caption reads "The action is a suggestion; the committee decides."
2. **Indicators.** Tiles without a heading, each with the derived mark:
   - **Priority level**: the level word, with the caption "worst of K2, K3, K6".
   - **K2 no activity**: the number of quarters, with the caption "counted after the start: 4 active quarters or a published launch".
   - **K3 handover clock**: the number of months, with the caption "since first announced handover date". If there is no announced date, the tile reads "no announced handover date". If the date has passed and the compound may be complete, the tile reads "date passed, may be handed over: confirm on site".
   - **K6 never started**: the number of months, with the caption "since first launch/promise, no construction start". If a construction start was observed, the tile reads "does not apply".
   - **K5 months eligible for review under contract terms**: the number of months, with the caption "the committee decides any action". If there is no published deadline, the tile reads "no published deadline".

   A missing value is shown as "unknown".
3. **The site now** (left). The latest Wayback capture with the caption "Latest capture · <date> · <stage>". In Track B, the buyer complaints chart (generated, orange mark) sits under it.
4. **Satellite curves** (right). A line chart of "Activity score A" and "Dynamic World built probability" for each quarter, on a 0 to 1 axis. Dashed markers show the quarter of a published developer statement, labelled "Developer statement published". Below the chart, the screen shows either "📌 First announced handover date: <month year> (the date K3 counts from)" or "📌 No announced handover date on file for this compound yet.". The caption reads "🔵 derived · gaps = quarters not assessable". If the series are missing, the screen says "Waiting for the A / Dynamic World series of CODE in real/kpi_values.parquet."
5. **More evidence.** A collapsed section, "More evidence: level history, image timeline, developer statements" (Track B adds ", money and classifier"). Inside, in this order:
   - **Level history.** A band of the level word for each quarter, with a legend.
   - **Construction stage by year.** A strip for each year with the stage word: "land or ground works", "under construction" or "complete". The caption reads "Construction first seen in <year>." If the stage table is not in the checkout, the screen says "The stage table (data/experiments/42_r7_stage_table) is not in this checkout."
   - **Wayback timeline.** A slider labelled **Capture date** shows one capture large, with the metrics **Captured** and "Stage in <year>" and the caption "N of M captures". Below it, **Compare two captures** offers two selectors, "Compare: from" and "Compare: to", each showing a capture with its date and stage. A capture with no stage shows "stage not on file". If there is no timeline, the screen says "No Wayback timeline for CODE in data/imagery/figures/timeline."
   - **Developer claims vs what space showed.** A table with the columns Published, Claim, Promised year and Nearest capture. Each row pairs a confirmed developer claim with the nearest capture within a year, or "none within a year". If none is confirmed, the screen says "No confirmed developer claim for CODE."
   - **Fine exposure, developer money and the classifier** (Track B only, generated).
   - **Inspection file** (Track B only). The button "📄 Inspection file (Arabic)" is disabled when no file is stored for the code and quarter, and the caption lists the codes that have stored files. When a file exists, the button reads "🟠 Open inspection file (Arabic HTML, includes generated figures)".
6. **Visit form.** See the section on the visit form below.

*Implementation note:* `screen_compound_file`, `render_compound_header`, `render_kpi_tiles`, `render_site_now`, `render_level_history`, `render_curves`, `render_stage_strip`, `render_images`, `render_claims`, `render_inspection_button`, `insights.k3_text`, `insights.short_reason`, `last_recorded_visit`.

## Screen 3: District view

Open **3 · District view**. The subtitle reads "What does the system give the committee?". The body of the screen does not use the track switch, so the view is the same in both tracks. If the KPI file is missing, the screen says "Waiting for real/kpi_values.parquet."

The screen shows these sections, in this order.

1. **An early signal.** The heading reads "An early signal: CODE" for one public late case, chosen as the case the stored case file flags earliest after construction started. The section shows the alert quarter, the months before its first handover date, what space saw, the level at the freeze date, what happened and any reported date, and two captures: "First capture after the alert" and "Latest". It shows one case only. If no case qualifies, the screen says "No public late case in the backtest was flagged after construction started."
2. **When the solution fails.** The backtest result ("the rule flagged N of 6 public late cases after construction started"; the bar set before testing was 5 of 6), a table of the two ways the missed cases looked, what it can do (compounds where a stall count at the level-2 threshold gave level 1 or 2) and the untested fix. Source: `data/experiments/35_backtest_diagnosis/DIAGNOSIS.md`.
3. **A false alarm against a missed case.** Four inputs with defaults from `configs/cost_assumptions.yaml` (cost of a false alarm, cost of a missed case, false alarms per year, missed cases per year), marked as assumptions. It shows how many false alarms one missed case is worth and the yearly cost of each error.
4. **Flagged now, before any handover date passed.** One line per compound on the visit list that has no announced handover date or whose K3 is zero, leaving out compounds that may be complete. Each line shows the code, the level text, the short reason and an **Open** button that opens the compound in screen 2. If none is flagged, the screen says "No compound on the visit list is flagged before a handover date."
5. **The developer said, space saw.** The compound furthest past its first announced date among those with confirmed claims. The line reads "CODE: as of <quarter>, N months past the first announced handover date (<month year>)." The section shows the claims table and two captures, "Nearest to the last claim" and "Latest". If none exists, it says "No compound has a confirmed developer claim."
6. **Homes in compounds eligible for review under contract terms.** A bar chart of published unit counts, with the axis "Homes (published unit count)" and each bar labelled with the number of months eligible for review under contract terms. The line reads "N homes in M compounds eligible for review under contract terms." The caption reads "Label = months eligible for review under contract terms." Generated unit counts are left out. If none qualifies, the screen says "No compound with a published unit count is eligible for review under contract terms."
7. **How late R7 promises ran.** A bar chart of months after the promised date for each public case with a delay, with a dashed median line. The line gives the number of cases, their range and the median. Cases with no value yet are listed with their outcome. The caption reads "Dashed line = median." If there is no delay on file, the screen says "No public case has a delay on file."
8. **Months eligible for review under contract terms.** A bar chart of months eligible for review under contract terms per compound. The line gives the total and the number of compounds. The caption reads "The committee decides any action." If none, the screen says "No compound has months eligible for review under contract terms."
9. **Developers with several compounds.** One row per developer code with two or more compounds. Each compound is an **Open** button labelled with its code and level text, most urgent first. If none, the screen says "No developer has more than one compound."
10. **Level history, all compounds.** A heat map with one row per compound, most urgent current level first, and one column per quarter.

*Implementation note:* `screen_district`, `render_early_warning`, `render_failures`, `render_alarm_tradeoff`, `insights.caught_cases`, `insights.stall_codes`, `insights.alarm_tradeoff`, `render_flagged_early`, `render_strongest_claim`, `render_homes_waiting`, `render_late_promises`, `render_fine_months`, `render_developer_groups`, `render_district_levels`, `insights.warning_case`, `insights.flagged_early`, `insights.strongest_claim`, `insights.homes_waiting`, `insights.late_delays`, `insights.fine_months`, `insights.developer_groups`, `insights.codes_by_current_level`.

## Screen 4: Digital twin what if

Open **4 · Digital twin what if**. The subtitle reads "Who would change if costs, collections or visit capacity changed?". This screen works only in Track B. In Track A it shows the warning "Digital twin what if uses generated data. Switch to Track B in the sidebar to open it." and nothing else.

Everything on this screen is generated, and the label "Synthetic - for training only" from the banner applies to it. Do not read these results as observed values, forecasts or validated figures. The screen does not change the stored priority levels.

The screen shows these parts, in this order.

1. **Progress against the baseline run.** A table with the columns Compound, Baseline progress %, S1 cost shock %, S1 change (pp), S2 collections drop % and S2 change (pp), for the latest month. The caption, marked 🟠 Generated, names the month and states that the baseline and both shocks come from one run. Below the table: "Change in percent points of progress. A shock that moves no compound to another level or visit-list place is a result, not a missing value." The shocks here move progress by about one percentage point. Do not read a larger change into this table.
2. **Tab S1 · Cost shock.** The caption, marked 🟠 Generated, gives the scenario "Imported cost +30%." and the month. If nobody crosses a threshold, the tab says "Nobody crosses a threshold: no compound changes level or list position." Otherwise it lists each changed compound with its hypothetical baseline level, its scenario level, "joins the list" or "leaves the list" where that applies, and the stored reason. A bar chart of level counts for the baseline and the scenario appears only when something changed.
3. **Tab S2 · Collections drop.** The same layout as S1, with the caption "Collections -25% for six months." and the same wording for no change.
4. **Tab S3 · Capacity.** Two boxes, "2 visits instead of 4" and "6 visits instead of 4". Each lists the compounds that join or leave the list, with the stored reason. If the list does not change, the box says "The list does not change." The caption shows the quarter. A capacity change moves list selection only; no level changes.
5. **Missing files.** A missing file shows "Waiting for ready-data/..." with the file name and the step that writes it.

The baseline label in the level chart is "Hypothetical baseline (generated finance)", and the scenario label is "Scenario".

*Implementation note:* `screen_what_if`, `render_progress_vs_baseline`, `render_finance_scenario`, `render_scenario_moves`, `render_scenario_levels`, `render_capacity_variant`, `insights.progress_view`, `insights.scenario_view`, `insights.level_counts`, `SCENARIO_TABS`, `SCENARIO_NOTES`, `CAPACITY_VARIANTS`.

## Visit form and recorded visits

The form is at the bottom of screen 2, under the heading **Visit form**. The card title is "📝 Record a visit". The caption reads "Pick the compound code. Do not write compound or developer names in the note."

Fields:

- **Code**: a list of the codes in the quarter, with the compound from screen 2 selected.
- **Date**: defaults to today. A later date cannot be chosen.
- **Result**: one of `progressing`, `stalled`, `complete` or `not done`.
- **Note**: optional free text, with the placeholder "Optional: what was seen on site."

Press **💾 Save visit** to save. A code that is not a code (for example a name) is refused with "Use a code such as C07 (codes only, no compound or developer names)." An empty code is refused with "Please enter a code before saving." A file error shows "Could not save the visit: <reason>". A saved visit shows "Visit saved for CODE (result, date)." and the form clears.

Each save adds one row to the visits file in the app data folder, and earlier rows are kept. The visits file is separate from the KPI file: a saved visit does not change the stored priority level.

Below the form, the card "🗒️ Recorded visits" shows three metrics, **Total visits**, **Latest visit** and **Stalled** ("N of total"), and a table of the visits, newest first, with the columns Code, Date, Result and Note. Its caption gives the path of the visits file. The card appears only when at least one visit is recorded. The latest recorded visit also appears in the screen 2 header.

*Implementation note:* `render_ops_visits_form`, `_render_form_card`, `_render_visits_card`, `append_visit`, `load_visits`, `validate_code`, `normalise_code`, `RESULT_OPTIONS` (src/dashboard/ops_visits.py); `last_recorded_visit` (app.py).

## Ask the chatbot

The chatbot is the hybrid RAG app in `chatbot/` (the dashboard has no built-in Q&A). The floating 💬 button at the bottom of the dashboard opens it at http://127.0.0.1:8001/, so start it first. On Linux/WSL: install uv (`curl -LsSf https://astral.sh/uv/install.sh | sh`), `git pull` and run `./start.sh` (same steps and first-run `chatbot/.env` stop as on Windows; the chatbot log is `chatbot/chatbot.log`); on Linux the chatbot uses CPU-only torch. If the chatbot is not running, the dashboard shows a note under the title saying so. On Windows: install uv once (`powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`), then `git pull` and `powershell -ExecutionPolicy Bypass -File .\start.ps1`; the script starts the chatbot (port 8001) and the dashboard (port 8501), and on the first run asks you to put the Gemini key in `chatbot\.env` (details in the README). By hand, from the repository root: `uv sync --locked --extra chatbot`, then `uv run --locked --extra chatbot uvicorn chatbot.app.api.main:app --port 8001` (set `SPACEYE_DB_PATH` to the v7 `spaceeye_ready.duckdb`). It answers about compounds, rules, complaints and visits, and about the sourced documents in `chatbot/knowledge/` (laws, decree, data-source and indicator notes), citing title, section and source link. Model calls are limited by the approval and budget in `configs/ai.yaml`; when they are off or used up, it gives a plain local answer. Its answers are not legal advice. After adding documents to `chatbot/knowledge/`, rebuild the index with `uv run --locked --extra chatbot python -m chatbot.app.retrieval.build_index --knowledge-only`.

## If a message appears

- **Waiting for real/kpi_values.parquet.** The KPI file is not in the app data folder. Screens 1 to 3 need it.
- **Waiting for the A / Dynamic World series of CODE ...** The satellite series for that compound are not in the KPI file.
- **Waiting for ready-data/...** A stored what-if file is missing. Screen 4 needs it.
- **real/compound_boundaries.geojson not found yet.** The priority map cannot be drawn in Track A.
- **Digital twin what if uses generated data. Switch to Track B ...** Screen 4 is open in Track A. Switch the track to see it.
- **CODE has no KPI row for <quarter> ...** The compound is not in the latest quarter, so it is shown as not assessable.
- **<label>: could not be read (<error type>).** A stored file could not be read. The rest of the screen still renders.
- **no_names gate: ... Display stopped.** A stored table has a value in a code column that is not a code. The screen stops.

*Implementation note:* `load_latest_kpis`, `render_map_slot`, `render_curves`, `screen_compound_file`, `screen_what_if`, `_safe`, `enforce_no_names`, `render_finance_scenario`.
