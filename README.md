# SpaceEye-GeoAI: Horus City Construction & Default Risk Radar

Current scope (28 October 2026): R7 construction monitoring and inspection priority for 12 coded compounds. The data release combines public observations, explicitly synthetic internal-operation tables, prepared data, a private binary training export and separate hypothetical financial scenarios.

Current contracts: [specifications](docs/requirements/01-specs.md), [dataset](docs/project-definition/03-dataset.md). Latest data-only handoff: `../Project/DATA_COMPLETION_FROM_SPECS.md`. Build data without model fitting: `uv run --locked --offline --with matplotlib python -m src.pipeline.complete_data`. Final audit: `../Project/app_data/release_audit.json`.

The older utilities/Oasis template below is retained as historical scaffolding; it does not describe the current R7 data release or its accepted results.

Internal decision-support platform for smart utilities, waste dispatch, and citizen triage. Combines energy, water, waste, and citizen-service data on a single trusted layer.

> **Synthetic data only — for spaceeye-geoai training, not operational use.** Every number is computed from the `ACUD_Oasis` dataset or marked as a target/hypothesis.

<p align="center">
  <img src="evals/figures/res1.png" alt="spaceeye-geoai — res1" width="45%">
  &nbsp; &nbsp;
  <img src="evals/figures/res2.png" alt="spaceeye-geoai — res2" width="45%">
</p>

<figure align="center">
  <img src="evals/figures/res.png" alt="res" width="80%">
  <figcaption>caption description</figcaption>
</figure>

how to adapt this project

1. Confirm project identity: SpaceEye-GeoAI (smart-city construction & risk radar).
2. Confirm dataset constraints and reference sources before implementation.
3. Move repeatable logic out of notebooks and into `src/`.
4. Keep tests small, deterministic, and focused on the critical path.


## Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [Setup](#setup)
  - [0. Prerequisites](#0-prerequisites)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Create Conda Environment](#2-create-conda-environment)
  - [3. Environment Variables](#3-environment-variables)
  - [4. Usage](#usage)
- [project structure](#project-structure)
- [Contributing](#contributing)
- [Author](#author)


## Overview
- **Problem:** District IOC watches utility and citizen feeds separately; one real event appears in multiple places; alarm fatigue and manual triage slow response.
- **Goal:** Detect energy waste, water leaks, bin overflows, and citizen-complaint clusters earlier — with one parent ticket per incident, zero personal-data leaks, and transparent AI recommendations.
- **Solution:** 4 operational modules (Energy, Water, Waste, Citizen Services) on a dual-schema (`raw_*` / `cleaned_*`) DuckDB layer + 5-tab Streamlit control room.
- **Results:** Benchmark tables, forecast error by season, Gemini vs keyword baseline accuracy, dispatch backtest (trips saved vs overflow), Data Trust Score.


## Key Features
* **Energy module:** Detects off-hours and weekend waste in government/CBD buildings using seasonal baselines (not fixed thresholds).
* **Water module:** Flags leaks from night-flow rise + pressure drop patterns, with a 5-step confirmation workflow.
* **Waste module:** Prioritises which bins need a truck today and which fixed-route trips can be cancelled safely.
* **Citizen Services module:** Routes Egyptian-Arabic complaints with Gemini triage (>73% keyword baseline target), masked personal data, and one parent ticket per cluster.


## Setup
0. Prerequisites
Before running this project, ensure you have the following installed:
* [Git](https://git-scm.com/)
* [Anaconda](https://www.anaconda.com/) or Miniconda
* Python 3.12 (recommended)
* Valid API Keys (if applicable)

1. Clone the Repository
```bash
git clone https://github.com/elsayedelmandoh/spaceeye-geoai
cd spaceeye-geoai
```

2. Create Conda Environment
```bash
# Create & activate the environment
conda create -n envname python=3.12 -y
conda activate envname

# Install pip and project dependencies
conda install pip -y
pip install -r requirements.txt
```

3. Environment Variables
Create a `.env` file at the project root and add your necessary API keys or configuration variables:
```bash
# Example .env file
API_KEY=your_api_key_here
```

Or copy .env.example file

```
# environment variables
cp .env.example .env
```

4. Usage — run locally
To start the Streamlit control room:
```bash
python app.py
```
Open the URL printed in the terminal. All 5 tabs load from `data/processed/oasis.duckdb`.

**Note:** The dashboard only shows data when the `cleaned_*` tables exist. If you see empty charts, run the data-quality audit notebook first (`notebooks/01_data_quality_audit.ipynb`).


## project structure

see `docs/project-definition/08-structure.md`


## Contributing
Contributions are welcome. Before contributing:
1. Confirm the dataset contract (`docs/project-definition/`) hasn't changed.
2. Run the data-quality audit (`tests/test_masking.py`, `tests/test_cleaning.py`).
3. Keep all user-facing output labelled `Synthetic data — spaceeye-geoai training only`.


## Authors

- **elsayed elmandoh** - NLP / LLM Engineer
- **verina fouad** - Applied AI / Machine Learning Engineer
- **ahmed abdelhamid** - Generative AI Engineer
- **nada shady** - AI Engineer
- **salma magdy** - Data Scientist

[![linkedin](https://img.shields.io/badge/elsayed-linkedin-0077b5?style=for-the-badge&logo=linkedin&logocolor=white)](https://www.linkedin.com/in/elsayed-elmandoh-b5849a1b8/)
[![linkedin](https://img.shields.io/badge/verina-linkedin-0077b5?style=for-the-badge&logo=linkedin&logocolor=white)](https://www.linkedin.com/in/verina-fouad/)
[![linkedin](https://img.shields.io/badge/ahmed-linkedin-0077b5?style=for-the-badge&logo=linkedin&logocolor=white)](https://www.linkedin.com/in/ahmed-abdelhameed-ai/)
[![linkedin](https://img.shields.io/badge/nada-linkedin-0077b5?style=for-the-badge&logo=linkedin&logocolor=white)](https://www.linkedin.com/in/nadashady/)
[![linkedin](https://img.shields.io/badge/salma-linkedin-0077b5?style=for-the-badge&logo=linkedin&logocolor=white)](https://www.linkedin.com/in/salma-magdy-ml/)
[![linkedin-post](https://img.shields.io/badge/post-linkedin-0077b5?style=for-the-badge&logo=linkedin&logocolor=white)]()
[![github](https://img.shields.io/badge/GitHub-repo-100000?style=for-the-badge&logo=github&logoColor=white)]()
