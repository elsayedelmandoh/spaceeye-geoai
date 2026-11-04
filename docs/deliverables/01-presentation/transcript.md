# Presentation transcript: who says what, slide by slide

The speaking plan for the 12-minute committee presentation ([presentation.pptx](presentation.pptx), 18 slides). Each member presents the part they built (owners from [02-team-roles-and-tasks.md](../../requirements/02-team-roles-and-tasks.md)). Times are the speaker-note times of the deck and add up to 12:00. Spoken text is about 130 words a minute (0:30 is about 65 words); say it in your own words, keep the numbers exact.

Rules for everyone: codes only (C18, never a name); "priority level", never "risk level"; never call a real compound "distressed"; K5 is "months eligible for review", never a fine; anything from Track B is "generated, synthetic, for training only".

## Running order

| # | Member | Slides | Time | Dashboard live |
| --- | --- | --- | --- | --- |
| 1 | Elsayed Elmandoh (lead) | 0 | 0:15 | - |
| 2 | Verina Fouad | 1, 2 | 1:00 | - |
| 3 | Ahmed Abdelhameed | 3, 4, 5 | 1:45 | - |
| 4 | Nada Shady | 6, 6b, 6c | 2:15 | Priority map → Compound file → visit form; search, filter, map click |
| 5 | Verina Fouad | 7 | 1:00 | District view (C21 early signal) |
| 6 | Elsayed Elmandoh | 8, 8b, 8c | 2:00 | Digital twin what if (Track B, S3 capacity); chatbot (💬) |
| 7 | Salma Magdy | 8d, 9 | 1:45 | - |
| 8 | Nada Shady | 10 | 0:45 | - |
| 9 | Ahmed Abdelhameed | 10b | 0:30 | - |
| 10 | Salma Magdy | 11 | 0:45 | - |
| | **Total** | **18 slides** | **12:00** | |

Per member: Elsayed 2:15, Verina 2:00, Ahmed 2:15, Nada 3:00, Salma 2:30 (sum 12:00).

## Before you start (10 minutes earlier)

- Two windows, one laptop: PowerPoint in presenter view, and one browser with the dashboard already loaded (start with `start.ps1`; dashboard on port 8501, chatbot on 8001).
- Four browser tabs, opened and scrolled in advance (each tab is its own session, so the track switch does not leak):
  1. Tab 1: **1 · Priority map**, Track A, scrolled to the top, search box empty, no filter set, no compound selected.
  2. Tab 2: **3 · District view**, at "An early signal: C21".
  3. Tab 3: Track B, **4 · Digital twin what if**, on the **S3 · Capacity** tab.
  4. Tab 4: the chatbot at http://127.0.0.1:8001/ (or use the 💬 button on the dashboard). Ask one question once before the talk so the embedding model is already loaded; the first question is slow. On a new machine the first run downloads the embedding model (intfloat/multilingual-e5-small), so start it the day before on a good connection.
- Switching: `Alt+Tab` from slides to browser, `Ctrl+1/2/3/4` for the tab, `Alt+Tab` back. Rehearse it; it should take under 2 seconds.
- Visit form: use a rehearsal copy of the app data folder, because a saved visit is a real row in the visits file.
- Backup: if the dashboard or the chatbot does not load, stay on the slide; slides 6, 6b, 7, 8b and 8c carry the same screens as screenshots. Say "here is the same screen" and continue. Never debug in front of the committee.
- One person (Nada) holds the mouse for every live part; the speaker talks, Nada clicks on cue (for Verina on slide 7 and Elsayed on slides 8b and 8c).

## How we switch speakers

Every handover is one sentence that names the next person and the question they answer, then the next speaker starts with the answer, not with "thank you". The outgoing speaker steps back; the next one is already standing next to the screen before the sentence ends.

---

## 1. Elsayed Elmandoh (team lead, AI component)

### Slide 0 · SpaceEye GeoAI (0:15)

**Say:**
"Good morning. We are SpaceEye GeoAI: New Capital Radar, for a company that owns a city. Thank you, Dr. Nadim Abdin, for supervising us. Today: which compounds your committee should visit first, and why."

**Handover:** "Verina will start with the problem, in your chairman's own numbers."

---

## 2. Verina Fouad (problem and decision framing)

### Slide 1 · Problem in numbers (0:30)

**Say:**
"These are your chairman's numbers, not ours: more than 400 developers, more than 500 projects, a field review every 3 months, about 7 to 8 percent seriously late, 6 mutual terminations. A committee cannot visit everything every cycle. So the question is: which compounds come first? Our answer is a short cycle list, with a reason for each."

### Slide 2 · The question and the decision (0:30)

**Say:**
"One district, R7: 12 coded compounds, quarter 2026Q3. Today every compound gets the same review every 3 months. Tomorrow: a list of at most 4 per cycle, each with one reason sentence, never a label on a developer. The observatory ranks; the committee decides. ACUD has not shared visit times, so today's cost is not measured."

**Handover:** "Where do these lists come from? Ahmed built the data and the rule."

---

## 3. Ahmed Abdelhameed (Track A: satellites, rule)

### Slide 3 · Data (0:30)

**Say:**
"Every number carries a colour: green real, blue derived, orange generated. 1,009 of 1,026 documented facts passed independent review. Public sources feed one prepared release of 84 frozen inputs, and the dashboard reads only that: 12 compounds, 516 compound-quarters, 57 statements. What only ACUD holds, like finance and supervisor reports, is generated and kept apart."

### Slide 4 · Seeing construction from space (0:30)

**Say:**
"Dynamic World gives the quarterly probability that a compound is being built: the activity score A. Open Buildings gives height as context only. Wayback gives dated before and after images. A quarter counts with at least 6 images and a reviewed boundary. Satellites see building, not interior finishing, so we never give a completion percentage."

### Slide 5 · The Track A rule (0:45)

**Say:**
"Three clocks. K2: quarters with no activity after construction started. K3: months since the first announced handover date. K6: months since a launch or promise with no construction start. The worst clock sets the level, no weights. Level 1 inspect now, 2 this cycle, 3 document review, 4 routine. If a compound may be complete, the level is capped at 3; this quarter that is C03, C12 and C21. Legal anchors, Decree 2184/2022: 12 months of grace, 24 months to the right to refund. K5, months eligible for review, never sets a level."

**Handover:** "That is the rule on paper. Nada will now show it working, live."

---

## 4. Nada Shady (dashboard)

### Slide 6 · Live demo, Track A (1:00)

**Switch:** `Alt+Tab` → Tab 1 (Priority map, Track A).

| Click | Show | Say |
| --- | --- | --- |
| 1 | Headline and the four tiles at the top | "This is what the committee opens each quarter. The headline already answers the question: these are this cycle's visits, and why the first one is first." |
| 2 | "This cycle's visits" cards (C18, C07, C14, C03) | "Four compounds from twelve, each with its level, its reason and the latest satellite capture with its date." |
| 3 | Visit list table and the **Cycle list (CSV)** button | "The list downloads in one click, with the reason in Arabic for the committee." |
| 4 | Sidebar → **2 · Compound file**, C18 | "Why this one? C18 is 57 months past the first announced handover date its clock counts from." |
| 5 | Scroll to **Visit form**: code C18, result, **Save visit** | "After the visit, the result is recorded here, by code only. Every saved visit builds the ground truth that does not exist today." |

**Say while moving on:** "All of this is real or derived; no generated number is on that map."

**Switch:** sidebar → **1 · Priority map** (stay in Tab 1).

### Slide 6b · Search, filters and map click (0:45)

Live on Tab 1, **Search and filters** section above the map. Slide 6b carries the same two screens as screenshots if the dashboard is slow.

| Click | Show | Say |
| --- | --- | --- |
| 1 | Type **C1** in **Search code** | "One search box takes a compound code or a developer code; a prefix works. Typing C1 leaves 6 of the 12 compounds on the map, and the legend shows the count for each level." |
| 2 | Pick a level in **Priority level** (for example level 1) | "Filters: quarter, level, developer, minimum K2, K3, K6, or the cycle list only. The rank stays the quarter's visit order." |
| 3 | Click one block on the map | "Click a block, and the sidebar opens that compound with its stored values and drill-downs." |
| 4 | The **Selected compound** panel in the sidebar | "Codes only, no names. One button opens its compound file." |
| 5 | Click **Clear selection**, then empty the search box | "Clear selection resets it." |

### Slide 6c · Four screens, one path from alert to action (0:30)

**Say (on the slide, no switch):**
"Four screens, four questions: whom first? Why this one? What does the system give, and when does it fail? And, generated, who changes if costs, collections or capacity change? The path: level, cycle list, compound file, visit form, recorded visit. Teammates' reviews changed the screens; the ten-second test with a committee member is still to be run."

**Switch:** `Alt+Tab` → slides (if still in the browser).

**Handover:** "Does it catch late projects early? Verina will show the backtest, with the clock frozen."

---

## 5. Verina Fouad (backtest)

### Slide 7 · Backtest: 1 of 6 and why (1:00)

**Say (on the slide):**
"We start with the miss. We froze the clock and replayed six real public R7 cases. The target, 5 of 6, was fixed before computing, not lowered, and not met: the rule alerted early in 1 of 6."

**Switch:** `Alt+Tab` → Tab 2 (District view, "An early signal: C21").

**Show and say:**

- Early-signal block: "This is the one hit, C21: the alert quarter and what space saw then."
- Scroll to **When the solution fails**: "In the five misses, imaging was sufficient, but the sites were active, so there was no stall to detect. The rule measures stalls and passed dates, not pace against a plan. Even the C21 hit came partly from publication timing, so we do not claim it carries over."

**Switch:** `Alt+Tab` → slides.

**Say:** "These counts do not prove why each delay happened; that needs ACUD's records."

**Handover:** "With ACUD's data, could a model do better? Elsayed shows what we tested on generated data."

---

## 6. Elsayed Elmandoh (Track B: generated data, what-if, chatbot)

### Slide 8 · Track B: generated data (0:45)

**Say:**
"Everything on this slide is synthetic, for training only. We asked: will a compound be distressed in the next six months? 96 training rows, 48 test rows, only 4 distressed test cases. The chart shows how many of those 4 each method put in its top 4. The public rule found 3; boosting on satellite data found 4, but that rests partly on height, and without height it drops to 1. A random list averages 0.335. With 4 cases the methods cannot be separated. This is a diagnostic, not real accuracy."

**Say as you move on:** "And what if the committee has a different number of visits? One scenario, live."

### Slide 8b · The observatory: one what-if scenario (0:30)

**Switch:** `Alt+Tab` → Tab 3 (Track B, Digital twin what if, S3 · Capacity). Point at the orange banner first.

**Show and say:**
"Orange banner: generated. What if the committee had 2 visits per cycle, or 6, instead of 4? Across all quarters, 45 of 744 rows change list membership, and no level ever changes. A dollar shock or a collections drop, S1 and S2, change nothing in the list. That is a result, not a missing value."

**Switch:** `Alt+Tab` → slides.

**Say as you move on:** "And can the committee simply ask the project a question? Live."

### Slide 8c · Ask the project: the chatbot (0:45)

**Switch:** `Alt+Tab` → Tab 4 (chatbot), or click the 💬 button on the dashboard.

| Click | Show | Say |
| --- | --- | --- |
| 1 | Type one question, for example "latest KPI for C18", and send | "The question goes to a router with 10 intents, then to two kinds of retrieval: facts from the v7 release and a search over statements, complaints and knowledge documents." |
| 2 | The answer and the sources it lists | "The answer comes with its sources and marks what is published, derived or generated. The AI model is used only when approved and within its call budget; otherwise the answer is local." |
| 3 | Ask a short follow-up without the code, for example "and the reason?" | "A follow-up keeps the last compound code, and generated items such as complaints stay labelled as synthetic." |

**Switch:** `Alt+Tab` → slides. If the chatbot is slow, close it and say "here is the same screen" on the slide.

**Handover:** "What does the assistant know, and where does it stop? Salma."

---

## 7. Salma Magdy (chatbot limits, value)

### Slide 8d · What the chatbot knows, and its limits (0:45)

**Say:**
"It knows 9 sourced documents: the ACUD site, Decree 2184/2022, Building Law 119, Law 151/2020, Dynamic World, Open Buildings, Esri Wayback, ISO 37120 and 37122, and our SLA note, plus the project's data. We tested it ourselves: 8 of 8 intent tests and 5 of 5 retrieval checks passed. They are small tests, not an accuracy claim. Model calls need the project owner's approval, at most 200 in total, then answers are local. Codes only, and it is not legal advice."

### Slide 9 · Value in EGP, 3 settings (1:00)

**Say:**
"Today's policy visits all 12. Visiting 4 per cycle means 16 visits a year. Under our assumptions the value is 0.007 to 0.102 million EGP a year. Three settings: a visit costs 2,000, 3,000 or 4,000 EGP, a team of three at published engineer pay plus transport. Operating cost and missed cases are public proxies; the cost of a late case is a placeholder of 20,000 EGP. Even the conservative setting is positive but small, and it is not a measured saving. We cannot yet measure a false alarm against a missed case; with ACUD's data, this becomes real."

**Handover:** "Value is one side; is it safe to use? Nada."

---

## 8. Nada Shady (risks and responsible use)

### Slide 10 · Risks and responsible use (0:45)

**Say:**
"Seven risks, and one control. A level is not a finding: it says whom to visit first, never misconduct or a sanction. Unknown stays unknown. Generated data never mixes with real data. Small samples are reported as counts, never percentages. Complaint text is masked, and real text needs further review. Law 151/2020 needs your data custodian's review. The handover pack is in the repository. The control in red: the committee decides, and every visit result is recorded."

**Handover:** "How does this run inside ACUD? Ahmed."

---

## 9. Ahmed Abdelhameed (production)

### Slide 10b · Launching in production (0:30)

**Say:**
"Three things: the dashboard, one quarterly data run, and the prepared release. Proposed, not deployed: a server inside ACUD's network, so data stays with ACUD and exports use codes only. Each quarter: refresh, quality gates, list, visits, recorded results. Any STOP blocks the release; the fallback is the simpler K1 check and the prior release."

**Handover:** "And what do we ask of you today? Salma closes with the decision."

---

## 10. Salma Magdy (decision)

### Slide 11 · Decision, transition and next step (0:45)

**Say (slow down; look at the committee, not the screen):**
"Our request is one decision: use the inspection priority list to choose which R7 compounds the committee visits first next cycle. The system recommends; the committee decides. Three phases: one pilot cycle while the current reviews continue, so going back costs nothing; then a small verified sample of ACUD data; then quarterly operation. This is what public data alone can do. Give us your data, and the demo parts become real operation. Thank you; we welcome your questions."

**End of the 12:00.** Leave slide 11 on screen during questions.

---

## Questions and answers (after the 12 minutes)

Elsayed takes each question, gives it to its owner in one sentence ("Ahmed built that, Ahmed?"), and closes if needed. The presenter of a slide may answer first about their own slide. Answers are one or two sentences, with the number, from [expected-questions.md](../expected-questions.md).

| Question type | Answers | Show if useful |
| --- | --- | --- |
| Satellites, rule, levels, backtest, "why not a score" | Ahmed | District view, Compound file |
| Generated data, model, what-if, complaints classifier | Verina | Tab 3 (what-if) |
| Screens, search and filters, wording, visit form, cycle list | Nada | Tab 1 |
| Money, KPIs, risks, law, governance, data request, chatbot knowledge and budget | Salma | Slides 8d, 9, 10 |
| AI, how the chatbot works, production, "what do you need from us" | Elsayed | Slide 8c, Tab 4 |

**Chatbot moment (Elsayed, about 30 seconds, when a question about the rules or the law comes up):**
Point back to slide 8c, then open the 💬 button on the dashboard (chatbot on port 8001) and type the committee's own question, for example "What does level 1 mean for C18?" or "What does Decree 2184/2022 say about the handover grace period?". Say: "This is the assistant from slide 8c. It answers from the project's data and its sourced documents and shows where each answer comes from. It is not legal advice, and it calls the AI model only within the budget the project owner approved." If it is slow, close it and answer yourself.

Ready one-liners:

- "Is this a real saving?" → "No, 0.007 to 0.102 million EGP a year under stated assumptions; your data makes it measurable."
- "Why only 1 of 6?" → "The rule detects stalls and passed dates; the five misses kept building, too slowly. We fixed the target before computing and did not lower it."
- "Are you calling developers distressed?" → "No. We say 'no building activity for N quarters' or 'passed its first date by N months', and the committee decides."
- "What do you need from us?" → "A coded export, starting with dated inspection and handover outcomes, the contract register and parcel geometry; ACUD keeps the identity mapping."
- "How do we start without risk?" → "One pilot cycle while the 3-month reviews continue; going back costs at most one rerun."
- "How accurate is the chatbot?" → "We do not claim an accuracy: 8 of 8 intent tests and 5 of 5 retrieval checks are our own small tests."

## What makes it land

- **Open on their numbers, close on their decision.** The first slide quotes the chairman; the last asks for one decision the committee can take next cycle.
- **Lead with the miss.** Saying "1 of 6, the target was fixed first" before anyone asks earns more trust than any good number.
- **Show, then say.** In the live parts, click first, pause one second, then speak about what is on screen.
- **One mouse, one voice.** Nada clicks every live part; the speaker never reaches for the laptop.
- **Same words as the screen.** Say "Inspect now", "months eligible for review", "Synthetic - for training only" exactly as the dashboard prints them.
- **Time.** Rehearse twice with a timer (T-ALL-05). If you run long, cut the Slide 4 detail and the Slide 10 list to three risks; never cut the decision on slide 11.
