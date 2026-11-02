# Wording audit: team documents (T-SA-07)

Date: 2 November 2026. Branch `docs/T-SA-07-audit-20261102b`, based on `origin/main`.
Reference: the allowed / not-allowed table in `docs/requirements/01-specs.md` section 3, plus the rules in the same section (origin marks, no names, generated data labelled, no unsupported accuracy claim).

## Scope and method

- Documents (12): `kpi-cards.md`, `method-card.md`, `expected-questions.md`, `knowledge-transfer.md`, `decision-memo.md`, `responsible-ai.md`, `governance-cards.md`, `user-guide.md`, `01-presentation.md`, `final-checklist.md`, `AI_AGENT_CONFIG.md`, `INSPECTION_DOSSIERS.md`. Each one was read in full.
- Text search first for the forbidden terms (distress, risk, fine, complete, %, progress, 3D, real-time, owe, speculat, floors, accuracy), then each hit was read in its sentence.
- Person names in the documents are noted by file and line only. They are not reproduced here.
- Verdicts: VIOLATION = breaks a rule of the table; CHECK = allowed in part or unclear, needs a wording decision or a fact check; SAFE = allowed wording, a caveat, or a denial.
- Not in scope: `data-request.md`, `quality-report.md`, `technical-track-a.md` and the other documents not in the list above.

## Findings

### A. AI_AGENT_CONFIG.md (Arabic, with English labels)

| # | File | Line | Text (as written, translated) | Rule | Verdict |
|---|---|---|---|---|---|
| E1 | AI_AGENT_CONFIG.md | 39 | "...combines top fluency with stable regex extraction, with an error rate of 0%." (Arabic: "بنسبة خطأ 0%") | Absolute accuracy claim with no measurement behind it. Spec section 3: no unsupported accuracy claim; section 14 rule on claims. The file has no test or log that measures the extraction error. | VIOLATION |
| E2 | AI_AGENT_CONFIG.md | 4, 11 | Approval and execution date "29 October 2026"; "the GenAI task is fully completed" (Arabic: "تم الانتهاء بالكامل") | Completion claim before any independent review. Task-board rule: "implemented, review pending" until a recorded review. Not a percentage, but an overclaim. | CHECK |
| E3 | AI_AGENT_CONFIG.md | 31 | "the top 5 compounds ... (capacity = 4-5)" | Scope is capacity 4 (spec section 2 and the team board). "4-5" contradicts the scope. | CHECK |
| E4 | AI_AGENT_CONFIG.md | 44 | Forbidden words: "distressed" may not be used on a real compound; "نسبة الإنجاز" (completion percentage) may not be used without a recorded observation | Quotes the rule itself as a prohibition | SAFE |
| E5 | AI_AGENT_CONFIG.md | 45 | "Use priority 1 or 2 as a neutral procedure, not 'risk level'" | Allowed term | SAFE |

Note on E1: the file says the "0%" error is a property of the extraction method. No evidence in the repo supports a rate of zero, so it stays a VIOLATION.

### B. method-card.md

| # | File | Line | Text | Rule | Verdict |
|---|---|---|---|---|---|
| M1 | method-card.md | 1, 4, 6, 8, 14 | Title "Binary distress model card"; "Approved target: distressed / not_distressed"; counts "7 distressed ... 4 distressed"; "distressed recall is 1 of 4" | Used for the generated Track B target only; the header says "Synthetic - for training only" | SAFE |
| M2 | method-card.md | 8 | "Not_distressed does not mean completed, continuously active or guaranteed financially healthy." | Denial, as required by the table | SAFE |
| M3 | method-card.md | 3 | A named reviewer in the header (name not reproduced) | Names are kept out of team exports and reports. A reviewer is a team member, not a compound or developer, so the rule is not broken, but the header should show a role. | CHECK |
| M4 | method-card.md | 14 | "AUC of 0.920 and 4 of 4 recall are tuned on the test split and are not reported as results" | Disclosed; no unsupported accuracy claim | SAFE |

### C. knowledge-transfer.md

| # | File | Line | Text | Rule | Verdict |
|---|---|---|---|---|---|
| K1 | knowledge-transfer.md | 3 | "The dashboard and the inspection agent are implemented and their review is pending" | `CLAUDE.md` says dashboard and inspection-agent functionality remain unfinished, and `app.py` and some helpers are scaffolds. The status is overstated. | CHECK |
| K2 | knowledge-transfer.md | 22 | "The approved classifier is binary distressed/not_distressed; use its normalized probabilities" | The sentence does not say the classifier runs on generated data only; a reader could apply it to real compounds. Add "generated data only". | CHECK |
| K3 | knowledge-transfer.md | 12, 16 | "Generated finances, complaints and fines"; "hypothetical priority tables" | Generated and labelled | SAFE |
| K4 | knowledge-transfer.md | 20 | "Unknown values stay null... Keep generated results distinct from real observations." | Rule text | SAFE |

### D. expected-questions.md

| # | File | Line | Text | Rule | Verdict |
|---|---|---|---|---|---|
| X1 | expected-questions.md | 8 | "Are you calling a developer distressed?" "No: we say 'no building activity for N quarters' ..." | Denial, uses the allowed phrases | SAFE |
| X2 | expected-questions.md | 9 | "Dynamic World matches Open Buildings (r about 0.96 on recomputed values) ... [verify in the dataset audit]" | Unverified figure with an open "verify" tag in a presentation answer. Remove or verify before use. | CHECK |
| X3 | expected-questions.md | 12, 13 | "4 distressed test cases"; "recall at 4 was 3 of 4 ..." | Counts on generated data, no percentages; caveat "scores are not accuracy claims" | SAFE |
| X4 | expected-questions.md | 14 | "Why no completion %?" "Images see roofs, not plaster and ceramics..." | Denial | SAFE |
| X5 | expected-questions.md | 17 | "Is K5 a fine?" "No: K5 counts months that would make a compound eligible for review under contract terms..." | Uses the allowed wording | SAFE |
| X6 | expected-questions.md | 21 | Complaints accuracy 0.27 / 0.22 / 0.37 / 0.30 | Accuracy figures on team-written texts; the same line says they do not prove real accuracy and that the model is a capability demo | SAFE |
| X7 | expected-questions.md | 16 | "from -0.006 to 0.098 million EGP per year ... every cost input is an assumption" | Caveat present | SAFE |

### E. decision-memo.md (English and Arabic)

| # | File | Line | Text | Rule | Verdict |
|---|---|---|---|---|---|
| DM1 | decision-memo.md | 9, 25 | "assigns a priority level (1-4)"; Arabic "مستوى أولوية" | Allowed term | SAFE |
| DM2 | decision-memo.md | 13, 29 | "The capacity-4 test holds 4 distressed rows" (Arabic: "4 صفوف متعثرة") | Generated data, labelled in the same paragraph | SAFE |
| DM3 | decision-memo.md | 19, 35 | "No compound is called distressed." Arabic: "لا نصف أي كومباوند بأنه متعثر" | Denial | SAFE |
| DM4 | decision-memo.md | 15, 31 | "from -0.006 to 0.098 million EGP per year ... every cost input is an assumption" | Caveat present | SAFE |
| DM5 | decision-memo.md | 19, 35 | "no completion % is given" | Denial | SAFE |

### F. responsible-ai.md

| # | File | Line | Text | Rule | Verdict |
|---|---|---|---|---|---|
| R1 | responsible-ai.md | 7 | "A priority level is not a finding of misconduct, legal distress, contractual breach or a verified fine." | Denial | SAFE |
| R2 | responsible-ai.md | 19 | "Current prediction scope is distressed/not_distressed; no completion class is predicted." | In the paragraph about synthetic data, the scope applies to generated labels | SAFE |
| R3 | responsible-ai.md | 17, 25 | "Annual height after 2024 is not an approved observation"; "do not describe estimated height as a survey, or interpret fine assumptions as actual legal amounts" | Matches the approved height context and the K5 caveat | SAFE |

### G. governance-cards.md

| # | File | Line | Text | Rule | Verdict |
|---|---|---|---|---|---|
| G1 | governance-cards.md | 10 | "Finance, complaints and fine assumptions ... Retain synthetic label; not actual finances, contracts, fines or complaints" | Generated and labelled | SAFE |
| G2 | governance-cards.md | 14 | "Visits and financial-priority exercises" | "Financial-priority" is a term drift; the table speaks of "priority level" for visits and does not use "financial priority". Rename to "financial scenario exercises". | CHECK |
| G3 | governance-cards.md | 3 | "No institutional approval or named-member sign-off is asserted." | Caveat | SAFE |

### H. user-guide.md

| # | File | Line | Text | Rule | Verdict |
|---|---|---|---|---|---|
| U1 | user-guide.md | 46 | "fine-eligible months and in how many compounds" (summary tile) | "Fine-eligible" is not in the allowed table; see the dashboard note D7. | CHECK |
| U2 | user-guide.md | 53 | "Suggested actions (monitor, document review, visit, written warning, fine review, confirm handover on site)" | "Written warning" and "fine review" are formal sanction-type labels on real compounds. Needs a wording decision (dashboard D54, D77). | CHECK |
| U3 | user-guide.md | 82, 84 | "Homes in compounds with fine-eligible months"; "Fine-eligible months by compound" | As U1 | CHECK |
| U4 | user-guide.md | 83 | "How late R7 handovers ran" | The dashboard heading is "How late R7 promises ran" (app.py line 1190). The screen name differs. | CHECK |
| U5 | user-guide.md | 86 | "Screen 4: Scenarios ... Open 4 · Scenarios in Track B" | The dashboard screen is "4 · Digital twin what if" (app.py line 69). The screen name differs. | CHECK |
| U6 | user-guide.md | 92 | Visit result "complete" among "progressing, stalled, complete, not done" | Same as dashboard D36. A visit result of "complete" on a real compound states a completion status; needs a decision. | CHECK |
| U7 | user-guide.md | 16, 24, 48, 64, 68, 88, 94 | Track B banner; generated tags; "the priority map is hidden in this track"; "K3 says 'date passed, may be handed over: confirm on site'"; "the contract decides any fine"; "generated, marked Synthetic - for training only"; "A visit entry does not change the stored priority level" | Caveats and origin labels present | SAFE |

### I. kpi-cards.md

| # | File | Line | Text | Rule | Verdict |
|---|---|---|---|---|---|
| KC1 | kpi-cards.md | 88, 92 | Card title "Fine exposure (policy screening months)"; purpose "How long has it been fine-eligible?" | The card is a screening count; the title "Fine exposure" and the purpose read as a fine. Allowed wording: "eligible for review under contract terms for N months". | CHECK |
| KC2 | kpi-cards.md | 133 | Tactical indicator "K5 eligible months" | Same family as KC1 | CHECK |
| KC3 | kpi-cards.md | 108, 125 | Card title "Never-started clock"; "K6 counts months without a confirmed observed start" | The title says "never started", a permanent claim. The body is correct ("not proof that no construction took place"). Allowed: "No construction start N months after the first launch". Change the title. | CHECK |
| KC4 | kpi-cards.md | 79 | K4 "Target 100%" | A target for assessability, not a completion percentage | SAFE |
| KC5 | kpi-cards.md | 28, 105, 138, 142, 161, 175, 189, 193, 195 | "does not measure completion or finishing"; "not an assessed legal fine"; "the term is 'priority level' ... never 'risk level'"; "not proof of completion and not a completion prediction"; "Generated signals are never used to label a real Track A compound as distressed"; "Counts only, no percentages"; "no completion % or finishing %" | Denials, caveats and the allowed term | SAFE |

### J. 01-presentation.md (slides 1-11)

| # | File | Line | Text | Rule | Verdict |
|---|---|---|---|---|---|
| P1 | 01-presentation.md | 3, 7-9 | Header rule: "Numbers ... carry an origin mark"; slide 1 numbers ("More than 400 developers and more than 500 projects"; "About 7-8% of developers seriously late; 6 mutual terminations") have no origin mark. They come from the chairman's statements, which the slide says. | Origin-mark rule of the document and spec section 3 | CHECK |
| P2 | 01-presentation.md | 22 | "1,009 of 1,026 documented facts passed independent review; 0 invented. This is the figure stated in the spec (section 12), not a recount." | An absolute "0 invented" figure with no recount behind it; the slide says so itself. Either recount or label as the spec's stated figure, without "0 invented". | CHECK |
| P3 | 01-presentation.md | 30 | "Open Buildings gives yearly heights to 2023; the 2024 value is an estimate, shown as context only" | The spec approves height context through 2024. The slide should say "approved context through 2024", not "estimate". | CHECK |
| P4 | 01-presentation.md | 33 | "No completion % or finishing % is given." | Denial | SAFE |
| P5 | 01-presentation.md | 37, 40 | "Priority level = the worst of K2, K3 and K6 ... K5 (fine-eligible months) is illustrative and never sets a level." | Allowed term; K5 caveat present. The label "fine-eligible months" is the KC1 issue. | SAFE |
| P6 | 01-presentation.md | 62-69 | Slide 8: "Target: distressed / not_distressed"; counts "4 distressed rows"; "Recall@4 ... 3 of 4" | Heading states "Track B: generated data (Synthetic - for training only)"; counts without percentages | SAFE |
| P7 | 01-presentation.md | 68 | "95% interval 0.000 to 0.750" | A statistical interval for the random baseline, not a completion percentage | SAFE |
| P8 | 01-presentation.md | 76 | "Scenarios: S1 dollar shock, S2 collections drop" | Matches the spec table (S1 "Dollar shock", USD/EGP +30%). The dashboard label "Imported cost +30%" differs (dashboard D64). Align the two. | CHECK |
| P9 | 01-presentation.md | 76 | "0 of 216 rows each"; "45 of 744 rows change list membership: 28 ... 17" | Counts; 28 + 17 = 45 | SAFE |
| P10 | 01-presentation.md | 78 | "Not a 3D or real-time observatory." | Denial | SAFE |
| P11 | 01-presentation.md | 85 | "Cost per visit (2,000 / 3,000 / 4,000 EGP) comes from a team of 3 at published engineer pay plus assumed transport." | The pay source is not cited on the slide. Cite it or mark the cost as an assumption. | CHECK |
| P12 | 01-presentation.md | 83, 86 | "from -0.006 to 0.098 million EGP per year"; "Not a measured saving." | Caveat present | SAFE |
| P13 | 01-presentation.md | 90, 95, 96 | "not a finding of misconduct, legal distress, contractual breach or a verified fine"; "Masking ... does not prove that every real name is removed"; "This is not legal advice." | Denials and caveats | SAFE |

### K. final-checklist.md

| # | File | Line | Text | Rule | Verdict |
|---|---|---|---|---|---|
| FC1 | final-checklist.md | 3, 9-21, 27, 36, 40-44 | "File present ... does not mean the deliverable is complete or reviewed"; "None of these is recorded as done."; "Not yet reviewed by the team." | Status wording avoids overclaims; no forbidden term | SAFE |

### L. INSPECTION_DOSSIERS.md

| # | File | Line | Text | Rule | Verdict |
|---|---|---|---|---|---|
| ID1 | INSPECTION_DOSSIERS.md | 5 | A person is named as the owner of the deliverable (name not reproduced) | Names are kept out of documents shared with the committee. Use the role. | CHECK |
| ID2 | INSPECTION_DOSSIERS.md | 7 | "Status: Completed & 100% Unit-Tested" | Completion claim before a recorded review; the board rule is "implemented, review pending". "100%" refers to tests, not to compounds, but it is an absolute claim. | CHECK |
| ID3 | INSPECTION_DOSSIERS.md | 49 | "Compound code, developer code, land area, allowed floors, authorized units." | "Allowed floors" is a permit field. The repo does not hold permitted floors (the data request to ACUD lists them, `01-presentation.md` line 103). The dossier must show "unknown" when the value is not held, never a number. | CHECK |
| ID4 | INSPECTION_DOSSIERS.md | 76 | "Ran 13 tests in tests/test_inference.py — OK." | Only 7 test names are listed above it (lines 68-74). Evidence mismatch. | CHECK |
| ID5 | INSPECTION_DOSSIERS.md | 33-36 | K5 "a policy screening indicator, never an assessed fine"; "correct (100% Pass)" | Caveat; "100% Pass" refers to the verifier check | SAFE |
| ID6 | INSPECTION_DOSSIERS.md | 28-31 | "Screening exposure (K5) 45 months" | Allowed count of months, labelled as screening | SAFE |
| ID7 | INSPECTION_DOSSIERS.md | 34-35 | A table body begins with no header row (a formatting defect, not a wording rule) | Not a wording rule; noted for the owner | CHECK |

## Counts

| File | VIOLATION | CHECK | SAFE |
|---|---|---|---|
| AI_AGENT_CONFIG.md | 1 | 2 | 2 |
| method-card.md | 0 | 1 | 3 |
| knowledge-transfer.md | 0 | 2 | 2 |
| expected-questions.md | 0 | 1 | 6 |
| decision-memo.md | 0 | 0 | 5 |
| responsible-ai.md | 0 | 0 | 3 |
| governance-cards.md | 0 | 1 | 2 |
| user-guide.md | 0 | 6 | 1 |
| kpi-cards.md | 0 | 3 | 2 |
| 01-presentation.md | 0 | 5 | 8 |
| final-checklist.md | 0 | 0 | 1 |
| INSPECTION_DOSSIERS.md | 0 | 5 | 2 |
| Total | 1 | 26 | 37 |

64 rows in all. A row that lists several lines (for example KC5, U7, FC1) counts once.

## Violations

1. `docs/deliverables/AI_AGENT_CONFIG.md:39` - an absolute "0%" error rate ("بنسبة خطأ 0%") for the regex extraction. No measurement in the repo supports it. Confirmed as a VIOLATION of the no-unsupported-accuracy-claim rule. Fix: remove the number, or give the measured rate and the test that produced it.

## Points for the owner

1. The "Fine-eligible" family appears in the user guide, the K5 card, the presentation and the dashboard (U1, U3, KC1, KC2, P5). The allowed phrase in the spec table should replace it everywhere, with the same wording on the dashboard.
2. Person names appear in the headers of two documents (M3, ID1). They are not reproduced here. The owner should replace them with roles.
3. Status overclaims (E2, K1, ID2) conflict with the task-board rule: "implemented, review pending" until a recorded review.
4. The screen names in the user guide (U4, U5) do not match the dashboard; fix the guide or the dashboard labels.
