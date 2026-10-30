# complaints_training

Synthetic - for training only

100rows. See COMPONENT_DATA_PROTOCOL.md for definitions and limits.

| Column | Type | Meaning |
| --- | --- | --- |
| complaint_id | str | Stable complaint identifier;SYN-B IDs belong only to the generated benchmark. |
| code | str | Compound code,key only,not text model input. |
| created_at | datetime64[us] | Synthetic complaint recording time. |
| channel | str | Recorded channel,key/context only,not text model input. |
| desk_category | str | Noisy recorded category,excluded from X. |
| text_ar | str | Masked Arabic complaint;the sole classification input. |
| synthetic_label | str | Synthetic - for training only |
| label_category | str | Target category only;five classes,not an input. |
| group_id | str | Connected template/duplicate-family group;never crosses a split. |
| split | str | Fixed train/validation/test assignment;not a model feature. |
