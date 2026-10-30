# sim_clean/complaints.parquet

Actual schema;1334rows. Synthetic - for training only

| Column | Type | Unit/range | Origin | Meaning/method |
| --- | --- | --- | --- | --- |
| complaint_id | str |  | key | key;  |
| code | str | registered compound codes plus a planted unknown code | key | Coded compound identifier; accepted prepared tables use registered R7 codes. Planted unknown codes occur only in raw/quarantined test inputs. |
| created_at | datetime64[us] | Africa/Cairo local time, no zone | generated | when the complaint was filed; uniform day, office-hours-heavy hour; defect 5 puts 5 rows before launch |
| channel | str | phone / portal / visit | generated | filing channel; 50 / 35 / 15 %; 5 % are the same buyer on a second channel within 7 days |
| category | str | delay / stoppage / payment / quality / other | generated | category as filed by the complaint desk; from the causing event; 10-15 % filed under a wrong category on purpose |
| text_ar | str | about 100 texts, the rest empty | generated | complaint text in Arabic written from templates (no LLM); 10 texts carry a planted fake phone number (defect 6); templates by true cause, spelling slips, mixed topics |
| synthetic_label | str | see meaning | generated/derived from generated | Synthetic - for training only; retained on generated products. |
