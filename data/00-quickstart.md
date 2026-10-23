# data directory

**propose:** central store for input data only -- raw sources through processed splits.

**input:** external datasets, api responses, user uploads, generated samples.

**output:** processed datasets ready for training and evaluation.

**pipeline map:**
- `raw/` -> full dataset
- `processed/` -> cleaned dataset
- `samples/` -> small-scale dataset (4 months)
- `curated/`, `instructions/` -> reference / label sets

> model outputs (weights, checkpoints, predictions) live in **`artifacts/`**.
