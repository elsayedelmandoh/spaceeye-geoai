## Repository Structure

```text
spaceeye-geoai/
├── README.md                          # 1-page overview + how to run (< 10 minutes from clean setup)
├── requirements.txt                   # duckdb, pandas, pyarrow, pandera, lightgbm, prophet, scikit-learn, streamlit, plotly,
│                                      # folium, pydeck, geopandas, google-genai, pydantic, sqlglot, openpyxl, pyyaml, chromadb, rank-bm25
├── .env.example                       # GEMINI_API_KEY=, MASK_SALT=, GEMINI_MODEL=   (never commit .env)
├── Makefile                           # make fixtures | synth | extend | checks | kpis | app | test
├── app/                               # [R5] app.py (Normal/Crisis switch, sidebar, 6 tabs), page registry
├── config/                            # [R5] cost_assumptions.yaml, kpis.yaml, thresholds.yaml, crisis_scenarios.yaml
│                                      # [R1] extension.yaml · [R4] rag.yaml
├── contracts/                         # Pydantic models + table schemas from §2.3 (frozen)
├── fixtures/                          # tiny schema-correct parquet per output file (each role commits its own)
├── data/                              # not committed
│   ├── lite/  full/  reference/
│   ├── synthetic/                     # [R2][R3][R5] generated tables + oasis_synthetic_inputs.xlsx
│   ├── extended/                      # [R1] Jan–Nov 2026
│   ├── processed/                     # oasis.duckdb (raw_* / cleaned_*)
│   └── outputs/                       # parquet outputs of §2.3
├── sql/kpis/                          # one .sql per KPI ($start, $end, $zone)
├── src/
│   ├── platform/                      # [R1] database.py, data_quality.py, cleaning.py, trust_score.py
│   ├── forecasting/                   # [R1] forecaster, benchmark, Dec 2026
│   ├── extension/                     # [R1] extend_2026.py
│   ├── energy/                        # [R2] K1, K2, K5, BLD-03 views, wasted-energy method
│   ├── water/                         # [R3] K3, K4, leak detector (anomaly.py), calibration of hydraulics
│   ├── maintenance/                   # [R3] K6 (BLD-01, BLD-04)
│   ├── citizen/                       # [R3] K7, baseline_rule.py, tfidf, parent_tickets.py
│   ├── twin/                          # [R2] engine.py, w1_hvac.py, w2_peak_shift.py · [R3] w3_valve.py
│   ├── synth/                         # [R2] energy.py · [R3] water.py · [R5] stories.py, drill overlay
│   ├── genai/                         # [R4] pii_masking.py, gemini_triage.py, ai_sql_assistant.py
│   ├── rag/                           # [R4] ingest.py, retrieve.py, answer.py
│   ├── agents/                        # [R4] orchestrator.py, agent_1..4, incident_state.py, trace
│   ├── reco/                          # [R5] recommendation_engine.py
│   ├── crisis/                        # [R5] crisis.py (SOP-CRS-01..04 runner)
│   └── handover/                      # [R5] handover.py
├── notebooks/
│   ├── 01_data_quality_audit.ipynb
│   ├── 02_kpi_seasonal_analysis.ipynb
│   ├── 03_forecasting_anomaly.ipynb
│   ├── 04_gemini_nlp_benchmark.ipynb
│   ├── 05_extended_horizon_forecast.ipynb
│   ├── 06_digital_twin_scenarios.ipynb
│   └── 07_rag_eval.ipynb
├── rag_corpus/                        # corpus_a_sop_compliance/, corpus_b_incident_memory/ (masked)
├── reports/                           # data_quality_report.xlsx, governance_cards/*.yaml, evaluation_results.md, savings_scenarios.xlsx
├── docs/                              # data_dictionary.xlsx, synthetic_data_dictionary.xlsx, kpi_investigation_matrix.md,
│                                      # shift_handover_playbook.md, governance_card.md, responsible_ai_card.md, model_cards.md,
│                                      # monitoring_plan.md, ai_verification_log.md, user_guide.md, knowledge_transfer.md,
│                                      # executive_decision_brief_en_ar.md, research_egypt_dst_2026.md, MASTER_GRADUATION_PLAN.md
├── deck/                              # 5-slide deck, demo script, backup recording
└── tests/
    ├── test_contracts.py              # every fixture conforms to its schema
    ├── test_masking.py                # 0 phones, 0 national IDs
    ├── test_cleaning.py               # Wh→kWh, °F→°C, DST 23h/25h, de-dup with row counts
    ├── test_quality_checks.py         # C01–C07, C13–C24, C26–C28 pass/fail on seeded cases; (sensor_id,timestamp), (building_id,timestamp), request_id uniqueness
    ├── test_kpi_acceptance.py         # BLD-04 0.567 / max 2; BLD-01 88.66% of 97; BLD-02 99.73%; BLD-03 0.217
    ├── test_synthetic.py              # seed reproducibility, schema vs dictionary, provenance tags, planted stories found
    ├── test_extension.py              # horizon tags, seed reproducibility, official counts unchanged, 2026 DST (23 h on 24 Apr, 25 h on 29 Oct)
    ├── test_twin.py                   # simulate() determinism, constraint checks, EGP low ≤ base ≤ high
    ├── test_sql_guard.py              # blocks INSERT/DROP/multi-statement/PII columns
    ├── test_schema.py                 # TriageResult validation
    ├── test_rag_citations.py          # every answer cites a chunk or returns no_source_found
    └── test_agents.py                 # allow-list, Pydantic state, no write before Approve
```