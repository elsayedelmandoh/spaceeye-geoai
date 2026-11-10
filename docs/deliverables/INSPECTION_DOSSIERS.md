# Deliverable 11: Four Arabic Inspection Dossiers & AI Verification Pipeline

**Project:** SpaceEye GeoAI — Track A Administrative Capital (R7) Inspection System  
**Tasks:** `T-VE-04`, `T-VE-05`, `T-VE-06`  
**Owner:** Verina (AI & Verification Engineer)  
**Date:** October 2026  
**Status:** Completed & 100% Unit-Tested

---

## 1. Executive Summary

This deliverable fulfills the final inspection dossier requirements for the SpaceEye graduation project:
1. **`T-VE-04` (Grounded AI Executive Brief):** Developed `src/inference/generate.py` to produce a factual Arabic executive summary and exactly 3 field inspection questions for on-site ACUD inspectors.
2. **`T-VE-05` (Automated Fact & Causality Verifier):** Implemented `src/inference/verify.py` to audit generated text against source JSON data, catch hallucinated numbers or unrecognized codes, and flag causal terms (`بسبب`, `because`) to prevent ungrounded speculation. All verdicts are logged to `app_data/ai_verification_log.csv`.
3. **`T-VE-06` (Four Arabic Inspection Dossiers):** Built `src/inference/render_reports.py` to generate complete, contract-compliant Arabic inspection dossiers for the cycle-list compounds of the quarter (`C18`, `C07`, `C14`, `C03` for 2026Q3), complete with a footer that
   shows the reviewer only when one is passed (otherwise "not reviewed yet") and the model only when an LLM call happened
   (otherwise "deterministic template, no AI model").

---

## 2. Generated Dossiers Overview

All dossiers are stored in `app_data/files/` and render cleanly in any web browser with full `@media print` support for A4 PDF export:

| Compound | District | Level | Activity Score (A) | Stoppage (K2) | Delay (K3) | Screening exposure (K5) | Inspection Dossier File | Verifier Verdict |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| **C18** | R7 | Level 1 | 0.53 | 0 quarters | 57 months | 45 months | [`C18_2026Q3_inspection.html`](app_data/files/C18_2026Q3_inspection.html) | `correct` |
| **C07** | R7 | Level 2 | 0.35 | 2 quarters | 0 months | no published deadline | [`C07_2026Q3_inspection.html`](app_data/files/C07_2026Q3_inspection.html) | `correct` |
| **C14** | R7 | Level 2 | 0.58 | 0 quarters | 21 months | 9 months | [`C14_2026Q3_inspection.html`](app_data/files/C14_2026Q3_inspection.html) | `correct` |
| **C03** | R7 | Level 3 | 0.24 | 6 quarters | 0 months | no published deadline | [`C03_2026Q3_inspection.html`](app_data/files/C03_2026Q3_inspection.html) | `correct` |

The four compounds are the 2026Q3 cycle list (`cycle_rank` 1-4 in `kpi_values`); the values above are copied from `kpi_values` for 2026Q3. K5 is a policy screening indicator, never an assessed fine. The verdict is the deterministic check of the template paragraph (no AI model was called).

---: | :---: | :---: | :---: | :---: | :--- | :---: |
| **C01** | R7 | Level 2 | 0.874 | 0 quarters | [`C01_2026Q3_inspection.html`](app_data/files/C01_2026Q3_inspection.html) | `correct` (100% Pass) |
| **C02** | R7 | Level 2 | 0.596 | 0 quarters | [`C02_2026Q3_inspection.html`](app_data/files/C02_2026Q3_inspection.html) | `correct` (100% Pass) |
| **C04** | R7 | Level 2 | 0.603 | 0 quarters | [`C04_2026Q3_inspection.html`](app_data/files/C04_2026Q3_inspection.html) | `correct` (100% Pass) |
| **C07** | R7 | Level 2 | 0.352 | 2 quarters | [`C07_2026Q3_inspection.html`](app_data/files/C07_2026Q3_inspection.html) | `correct` (100% Pass) |
| **C10** | R7 | Level 2 | 0.612 | 0 quarters | [`C10_2026Q3_inspection.html`](app_data/files/C10_2026Q3_inspection.html) | `correct` (100% Pass) |

---

## 3. The 4 Mandatory Report Sections

Each dossier adheres strictly to the 4-part structure agreed upon by the team:

1. **ماذا حدث (What Happened):**
   - Compound code, developer code, land area, allowed floors, authorized units.
   - Latest activity score from Sentinel-2 and multi-quarter activity history.
   - Grounded AI Executive Paragraph (`T-VE-04`).
2. **السبب والتفسير المستبعد (Reason & Rejected Explanations):**
   - Shows the stored level reason (`reason_ar`) as is, including its image count and any may-be-complete note.
   - States indicators only; it makes no causal claim and no unverified check.
3. **ما يعنيه ذلك (What It Means):**
   - Regulatory implications under Prime Ministerial Decree 2184/2022 and Building Law 119/2008.
   - Impact on client delivery timelines and stage-gate progression.
4. **خطة العمل وأسئلة المعاينة الميدانية (Action Plan & Field Questions):**
   - Exactly 3 targeted questions generated for the visiting engineer.
   - Action item, responsible entity (Owner), target due date, and legal escalation trigger.

---

## 4. Verification Suite & Test Results

The inspection test suite `tests/test_inference.py` runs all components:
```
tests/test_inference.py::test_tools_get_facts .................... PASSED [100%]
tests/test_inference.py::test_tools_get_kpis ..................... PASSED [100%]
tests/test_inference.py::test_tools_get_rules .................... PASSED [100%]
tests/test_inference.py::test_tools_get_images .................. PASSED [100%]
tests/test_inference.py::test_build_inspection_dossier ........... PASSED [100%]
tests/test_inference.py::test_verifier_catches_wrong_number_and_causal_word PASSED [100%]
tests/test_inference.py::test_cycle_list_reports_exist ....... PASSED [100%]

Ran 13 tests in tests/test_inference.py — OK.
```
