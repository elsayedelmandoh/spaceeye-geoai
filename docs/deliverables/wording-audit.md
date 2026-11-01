# Wording audit

Task T-SA-07. Checks every document written under T-SA-02, T-SA-03, T-SA-05, T-SA-06 and T-SA-09 against the allowed / forbidden table in `docs/requirements/01-specs.md` (section 3). Result: no violation found in the files below. Draft for review.

## Scope and method

Checked: `docs/deliverables/kpi-cards.md`, `configs/kpis.yaml`, `configs/cost_assumptions.yaml`, `docs/deliverables/decision-memo.md`, `docs/deliverables/01-presentation.md`, `docs/deliverables/expected-questions.md`.

Method: a text search for the forbidden terms, then each hit was read in its sentence and judged as a violation or as a safe use (a denial, a caveat or a data-request item). The last two files were read from their pull-request branches, because they were not on `main` at the time.

Not checked: other team documents, the dashboard screens, and the deck itself (not yet built).

## Checklist

- [x] No "risk level" or "high-risk developer" used. The term appears only in a sentence that forbids it (`kpi-cards.md`) and in the slides' opening note.
- [x] No "distressed" about a real compound. It appears only for the Track B target on generated data ("distressed / not_distressed", "4 distressed test rows") or in a denial ("no compound is called distressed").
- [x] No completion % or finishing % from images. Every hit says that none is given.
- [x] No "fined", "owes X EGP" or "land speculator". K5 is worded "fine-eligible" and "not an assessed legal fine".
- [x] No "3D / real-time digital twin". Slide 8b says "Not a 3D or real-time twin".
- [x] No height number and no 2025/2026 height claim. "2026Q3" is only the reporting quarter.
- [x] No "8 floors built". "Permitted floors" appears only as an item in the data request to ACUD.
- [x] The retired figures 92% / 62% / 37% appear nowhere.
- [x] No unsupported accuracy claim. Track B scores are always described as diagnostic on generated data, with the denominator (n of 4), capacity 4 and the random baseline.
- [x] Backtest quoted as counts only (1 of 6 after-start, 0 of 6 point-in-time), with the criterion of 5 cases "not lowered, not achieved".
- [x] Value in EGP quoted only as "under these assumptions, from -0.006 to 0.098 million EGP per year", with every cost input marked as an assumption.
- [x] Codes only, no compound or developer names (by inspection of the files; the project's own `no_names` gate covers generated outputs).

## Points for the reviewer

1. "distressed" appears next to "generated data" each time it is used for Track B. Is that enough, or is another wording preferred?
2. K5 keeps the spec's wording "fine exposure" and "fine-eligible". The allowed table suggests "eligible for review under contract terms for N months". Should the card titles follow it?
3. Should the audit also cover other team documents and the dashboard screens? The task says "every doc, slide and screen"; this PR covers only the files above.
4. A text search cannot detect an unknown name, so the codes-only rule is checked by reading, not by the search.
