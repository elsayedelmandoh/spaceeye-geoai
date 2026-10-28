# synthetic_visits

Synthetic - for training only

58rows. See COMPONENT_DATA_PROTOCOL.md for definitions and limits.

| Column | Type | Meaning |
| --- | --- | --- |
| visit_id | str | Unique generated inspection record,key only. |
| code | str | Compound code,key only,not text model input. |
| source_quarter | str | Quarter whose generated state is carried to the assumed visit. |
| visit_date | datetime64[us] | Generated working date5–14days after cutoff,not an actual visit. |
| inspector_code | str | Fictional inspector code,I01–I03. |
| result | str | Generated progressing/stalled/complete/not_done status;not independent field validation. |
| note | str | Generated follow-up note,not a factual field report. |
| state_basis | str | Explicitly generated cutoff-state carry-forward. |
| origin | str | Generated/derived provenance,not actual observations. |
| synthetic_label | str | Synthetic - for training only |
