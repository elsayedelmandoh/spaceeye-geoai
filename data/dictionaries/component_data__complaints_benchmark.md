# complaints_benchmark

Synthetic - for training only

296rows. See COMPONENT_DATA_PROTOCOL.md for definitions and limits.

| Column | Type | Meaning |
| --- | --- | --- |
| complaint_id | str | Stable complaint identifier;SYN-B IDs belong only to the generated benchmark. |
| text_ar | str | Masked Arabic complaint;the sole classification input. |
| label_category | str | Target category only;five classes,not an input. |
| split | str | Fixed train/validation/test assignment;not a model feature. |
| template_ids | str | Generation-family IDs;disjoint between benchmark splits,not model inputs. |
| mixed_topic | bool | Secondary topic present;primary body determines label,evaluation metadata only. |
| origin | str | Generated/derived provenance,not actual observations. |
| synthetic_label | str | Synthetic - for training only |
