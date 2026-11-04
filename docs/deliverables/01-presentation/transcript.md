# Presentation transcript: who says what, slide by slide

The speaking plan for the 12-minute committee presentation ([presentation.pptx](presentation.pptx), 14 slides). Each member presents the part they built (owners from [02-team-roles-and-tasks.md](../../requirements/02-team-roles-and-tasks.md)). Times are the speaker-note times of the deck and add up to 12:00. Spoken text is about 130 words a minute; say it in your own words, keep the numbers exact.

Rules for everyone: codes only (C18, never a name); "priority level", never "risk level"; never call a real compound "distressed"; K5 is "months eligible for review", never a fine; anything from Track B is "generated, synthetic, for training only".

## Running order

| # | Member | Slides | Time | Dashboard live |
| --- | --- | --- | --- | --- |
| 1 | Elsayed Elmandoh (lead) | 0 | 0:15 | - |
| 2 | Verina Fouad | 1, 2 | 1:30 | - |
| 3 | Ahmed Abdelhameed | 3, 4, 5 | 2:15 | - |
| 4 | Nada Shady | 6 | 1:15 | Priority map → Compound file → visit form |
| 5 | Salma Magdy | 7 | 1:30 | District view (C21 early signal) |
| 6 | Verina Fouad | 8 | 1:00 | - |
| 7 | Elsayed Elmandoh | 8b | 0:30 | Digital twin what if (Track B, S3 capacity) |
| 8 | Salma Magdy | 9, 10 | 2:30 | - |
| 9 | Ahmed Abdelhameed | 10b | 0:30 | - |
| 10 | Nada Shady | 11 | 0:45 | - (chatbot kept for Q&A) |
| | **Total** | **14 slides** | **12:00** | |

Per member: Elsayed 0:45, Verina 2:30, Ahmed 2:45, Nada 2:00, Salma 4:00.

## Before you start (10 minutes earlier)

- Two windows, one laptop: PowerPoint in presenter view, and one browser with the dashboard already loaded (start with `start.ps1`; dashboard on port 8501, chatbot on 8001).
- Three browser tabs, opened and scrolled in advance (each tab is its own session, so the track switch does not leak):
  1. Tab 1: **1 · Priority map**, Track A, scrolled to the top.
  2. Tab 2: **3 · District view**, at "An early signal: C21".
  3. Tab 3: Track B, **4 · Digital twin what if**, on the **S3 · Capacity** tab.
- Switching: `Alt+Tab` from slides to browser, `Ctrl+1/2/3` for the tab, `Alt+Tab` back. Rehearse it; it should take under 2 seconds.
- Visit form: use a rehearsal copy of the app data folder, because a saved visit is a real row in the visits file.
- Backup: if the dashboard does not load, stay on the slide; slides 6, 7 and 8b carry the same screens as screenshots. Say "here is the same screen" and continue. Never debug in front of the committee.
- One person (Nada) holds the mouse for every live part; the speaker talks, Nada clicks on cue (for Salma on slide 7 and Elsayed on slide 8b).

## How we switch speakers

Every handover is one sentence that names the next person and the question they answer, then the next speaker starts with the answer, not with "thank you". The outgoing speaker steps back; the next one is already standing next to the screen before the sentence ends.

---

## 1. Elsayed Elmandoh (team lead, AI component)

### Slide 0 · SpaceEye GeoAI (0:15)

**Say:**
"Good morning. We are SpaceEye GeoAI: New Capital Radar, for a company that owns a city. Thank you, Dr. Nadim Abdin, for supervising us. In twelve minutes we will show you one thing: which compounds your committee should visit first, and why."

**Handover:** "Verina will start with the problem, in your chairman's own numbers."

---

## 2. Verina Fouad (problem and decision framing)

### Slide 1 · Problem in numbers (0:45)

**Say:**
"These are not our numbers. They are your chairman's: more than 400 developers, more than 500 projects, a field review every 3 months, about 7 to 8 percent of developers seriously late, and 6 mutual terminations. With that many projects and one review every quarter, a committee cannot visit everything every cycle. So the real question is not 'is anyone late', it is: which compounds come first? Our answer is a short cycle list, with a reason for each compound."

### Slide 2 · The question and the decision (0:45)

**Say:**
"We took one district, R7: 12 coded compounds, reporting quarter 2026Q3. Today every compound gets the same review every 3 months. Tomorrow the committee gets a list of at most 4 compounds per cycle, each with one reason sentence, such as 'no building activity since a given quarter'. Never a label on a developer. The observatory ranks; the committee decides. One honest note: ACUD has not shared visit times or missed cases, so today's cost of the current process is not measured."

**Handover:** "Where do these lists come from? Ahmed built the data and the rule."

---

## 3. Ahmed Abdelhameed (Track A: satellites, rule)

### Slide 3 · Data (0:45)

**Say:**
"Every number you will see carries a colour: green is real, blue is derived from real data, orange is generated. 1,009 of 1,026 documented facts passed independent review. The pipeline is simple: public sources and statements go into one prepared release of 84 frozen inputs, and the dashboard reads only that. 12 compounds, 516 compound-quarters from 2016 to 2026, 57 developer statements. What only ACUD holds, like finance and supervisor reports, is generated and kept apart."

### Slide 4 · Seeing construction from space (0:30)

**Say:**
"Dynamic World gives us, every quarter, the probability that a compound is being built: that is the activity score A. Open Buildings gives height as context only. Wayback images give before and after pictures with their dates. A quarter counts only with at least 6 images and a reviewed boundary. And the limit, clearly: satellites see building, not interior finishing. We never give a completion percentage."

### Slide 5 · The Track A rule (1:00)

**Say:**
"The rule has three clocks. K2: quarters with no activity after construction started. K3: months since the first announced handover date. K6: months since a launch or promise with no construction start. The worst clock sets the level, with no weights, because a score out of 100 would claim a precision we do not have. Level 1 inspect now, level 2 this cycle, level 3 document review, level 4 routine. If a compound may already be complete, the level is capped at 3; this quarter that applies to C03, C12 and C21. The legal anchors are Decree 2184/2022: 12 months of handover grace, 24 months to the right to refund. K5, months eligible for review, is shown but never sets a level."

**Handover:** "That is the rule on paper. Nada will now show it working, live."

---

## 4. Nada Shady (dashboard)

### Slide 6 · Live demo, Track A (1:15)

**Switch:** `Alt+Tab` → Tab 1 (Priority map, Track A).

| Click | Show | Say |
| --- | --- | --- |
| 1 | Headline and the four tiles at the top | "This is what the committee opens each quarter. The headline already answers the question: these are this cycle's visits, and why the first one is first." |
| 2 | "This cycle's visits" cards (C18, C07, C14, C03) | "Four compounds, from twelve. Each card has its level and its reason, and the latest satellite capture with its date." |
| 3 | The 3D map, click one block | "Colour is the priority level, grey is not assessable. Height is building height, as context only." |
| 4 | Visit list table and the **Cycle list (CSV)** button | "The list downloads in one click, with the reason in Arabic for the committee." |
| 5 | Sidebar → **2 · Compound file**, C18 | "Why this one? C18: the three clocks, the satellite curve, and the first announced handover date the clock counts from. C18 is 57 months past it." |
| 6 | Scroll to **Visit form**: code C18, result, **Save visit** | "After the visit, the result is recorded here, by code only. Every saved visit builds the ground truth that today does not exist." |

**Say while switching back:** "Everything you just saw in Track A is real or derived; there is no generated number on that map."

**Switch:** `Alt+Tab` → slides.

**Handover:** "Does it catch late projects early? Salma will show the backtest, with the clock frozen."

---

## 5. Salma Magdy (KPIs, value, governance)

### Slide 7 · Backtest: 1 of 6 and why (1:30)

**Say (on the slide):**
"We start with the miss. We froze the clock and replayed six real public R7 cases that ended up late. We fixed the target before computing: 5 of 6. We did not lower it, and we did not meet it. The rule alerted early in 1 of 6."

**Switch:** `Alt+Tab` → Tab 2 (District view, "An early signal: C21").

**Show and say:**

- Early-signal block: "This is the one hit, C21: the alert quarter, what space saw with the data available at that time, and the capture after the alert next to the latest one."
- Scroll to **When the solution fails**: "And this is the honest part. In the five misses, imaging was sufficient, at least 10 images per quarter, but the sites were active, so there was no stall to detect. The rule measures stalls and passed dates, not pace against a plan. Even the C21 hit came partly from publication timing, so we do not claim it carries over."

**Switch:** `Alt+Tab` → slides.

**Say:** "These counts do not prove why each delay happened; that needs ACUD's records."

**Handover:** "With ACUD's data, could a model do better? Verina tested that on generated data."

---

## 6. Verina Fouad (Track B: generated data)

### Slide 8 · Track B: generated data (1:00)

**Say:**
"Everything on this slide is synthetic, for training only. We generated ACUD-style finance, reports and complaints, and asked one question: will a compound be distressed in the next six months? We had 96 training rows and 48 test rows, with only 4 distressed test cases. The chart shows how many of those 4 each method put in its top 4. The public rule found 3, boosting on satellite data found 4, but that 4 rests partly on height, and without height it drops to 1. A random list scores 0.335 on average. Our honest reading: with 4 cases the methods cannot be separated, and adding ACUD-style data did not clearly help. This is a diagnostic, not real accuracy."

**Handover:** "What changes if the committee has a different number of visits? Elsayed shows one scenario."

---

## 7. Elsayed Elmandoh (what-if)

### Slide 8b · The observatory: one what-if scenario (0:30)

**Switch:** `Alt+Tab` → Tab 3 (Track B, Digital twin what if, S3 · Capacity). Point at the orange banner first.

**Show and say:**
"Orange banner: generated. The question here is: what if the committee had 2 visits per cycle instead of 4, or 6? These boxes show who joins or leaves the list. Across all quarters, 45 of 744 rows change list membership, and no level ever changes. A dollar shock or a collections drop, S1 and S2, change nothing in the list. A result, not a missing value."

**Switch:** `Alt+Tab` → slides.

**Handover:** "So what is all this worth in money? Salma."

---

## 8. Salma Magdy (value, risks)

### Slide 9 · Value in EGP, 3 settings (1:30)

**Say:**
"We compare against today's policy of visiting all 12. Visiting 4 per cycle means 16 visits a year. Under our assumptions the value ranges from 0.007 to 0.102 million EGP a year. Three settings: a visit costs 2,000, 3,000 or 4,000 EGP, a team of three at published engineer pay plus transport. The operating cost and missed cases are public proxies; the cost of a late case is a placeholder of 20,000 EGP. Even the conservative setting is positive, but it is small, and it is not a measured saving. What we cannot measure yet is the cost of a false alarm against a missed case; with ACUD's data, this slide becomes real."

### Slide 10 · Risks and responsible use (1:00)

**Say:**
"Seven risks, and one control. A level is not a finding: it says whom to visit first, never misconduct or a sanction. Unknown stays unknown: missing evidence never counts against anyone. Generated data never mixes with real data. Small samples are reported as counts, never percentages. Complaint text is masked, and no external AI call reads it. Law 151/2020 needs your data custodian's review. And the handover pack is in the repository. The control in red: the committee decides, and every visit result is recorded."

**Handover:** "How does this run inside ACUD? Ahmed."

---

## 9. Ahmed Abdelhameed (production)

### Slide 10b · Launching in production (0:30)

**Say:**
"Technically it is three things: the dashboard, one quarterly data run, and the prepared release. Proposed, not deployed: a server inside ACUD's network, so data stays with ACUD and exports use codes only. Every quarter: refresh, quality gates, list, visits, recorded results. Any STOP blocks the release, and the fallback is the simpler K1 check and the prior release. The chatbot calls the AI model only within an approved budget."

**Handover:** "And what do we ask of you today? Nada closes with the decision."

---

## 10. Nada Shady (decision)

### Slide 11 · Decision, transition and next step (0:45)

**Say (slow down; look at the committee, not the screen):**
"Our request is one decision: use the inspection priority list to choose which R7 compounds the committee visits first next cycle. The system recommends; the committee decides. We propose three phases: one pilot cycle while the current reviews continue, so going back costs nothing; then a small verified sample of ACUD data; then quarterly operation. This is what public data alone can do. Give us your data, and the demo parts become real operation. Thank you; we are happy to take your questions."

**End of the 12:00.** Leave slide 11 on screen during questions.

---

## Questions and answers (after the 12 minutes)

Elsayed takes each question, gives it to its owner in one sentence ("Ahmed built that, Ahmed?"), and closes if needed. The presenter of a slide may answer first about their own slide. Answers are one or two sentences, with the number, from [expected-questions.md](../expected-questions.md).

| Question type | Answers | Show if useful |
| --- | --- | --- |
| Satellites, rule, levels, backtest, "why not a score" | Ahmed | District view, Compound file |
| Generated data, model, what-if, complaints classifier | Verina | Tab 3 (what-if) |
| Screens, wording, visit form, cycle list | Nada | Tab 1 |
| Money, KPIs, risks, law, governance, data request | Salma | Slides 9, 10 |
| AI, chatbot, production, "what do you need from us" | Elsayed | Chatbot |

**Chatbot moment (Elsayed, about 30 seconds, when a question about the rules or the law comes up):**
Open the 💬 button on the dashboard (chatbot on port 8001) and type the committee's own question, for example "What does level 1 mean for C18?" or "What does Decree 2184/2022 say about the handover grace period?". Say: "This is our assistant. It answers from the project's data and its sourced documents and shows where each answer comes from. It is not legal advice, and it calls the AI model only within the budget ACUD approves." If it is slow, close it and answer yourself.

Ready one-liners:

- "Is this a real saving?" → "No, 0.007 to 0.102 million EGP a year under stated assumptions; your data makes it measurable."
- "Why only 1 of 6?" → "The rule detects stalls and passed dates; the five misses kept building, too slowly. We fixed the target before computing and did not lower it."
- "Are you calling developers distressed?" → "No. We say 'no building activity for N quarters' or 'passed its first date by N months', and the committee decides."
- "What do you need from us?" → "A coded export, starting with dated inspection and handover outcomes, the contract register and parcel geometry; ACUD keeps the identity mapping."
- "How do we start without risk?" → "One pilot cycle while the 3-month reviews continue; going back costs at most one rerun."

## What makes it land

- **Open on their numbers, close on their decision.** The first slide quotes the chairman; the last asks for one decision the committee can take next cycle.
- **Lead with the miss.** Saying "1 of 6, the target was fixed first" before anyone asks earns more trust than any good number.
- **Show, then say.** In the live parts, click first, pause one second, then speak about what is on screen.
- **One mouse, one voice.** Nada clicks every live part; the speaker never reaches for the laptop.
- **Same words as the screen.** Say "Inspect now", "months eligible for review", "Synthetic - for training only" exactly as the dashboard prints them.
- **Time.** Rehearse twice with a timer (T-ALL-05). If you run long, cut the Slide 4 detail and the Slide 10 list to three risks; never cut the decision on slide 11.
