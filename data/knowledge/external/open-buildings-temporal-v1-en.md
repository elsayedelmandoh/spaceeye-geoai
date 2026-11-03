---
title: "Open Buildings 2.5D Temporal V1 (Google Earth Engine dataset catalog)"
source_url: "https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_Research_open-buildings-temporal_v1"
retrieval_date: "2026-11-02"
kind: "satellite-data"
language: "en"
notes: "Official dataset page; licence CC-BY 4.0 or ODbL v1.0 (user's choice)."
---

# Open Buildings Temporal V1

The Open Buildings 2.5D Temporal Dataset contains data about building presence, fractional building counts and building heights at an effective spatial resolution of 4 m (rasters are provided at 0.5 m resolution) at an annual cadence from 2016 to 2023. It is produced from open-source, low-resolution imagery from the Sentinel-2 collection. It covers Africa, South Asia, South-East Asia, Latin America and the Caribbean.

## Bands (pixel size 4 metres)
- building_fractional_count: source data for deriving building counts for a given area.
- building_height (m): building height relative to the terrain, range 0 m to 100 m.
- building_presence: model confidence that the pixel is part of a building, range 0.0 to 1.0. The values are uncalibrated: a confidence of 0.8 does not mean an 80% likelihood of a building. They can be used only for relative ranking or thresholding, and can vary across location and time with cloud cover and imagery misalignment.

## Terms of use
Shared under Creative Commons Attribution (CC-BY 4.0) and the Open Data Commons Open Database License (ODbL) v1.0; the user picks one. Leverages Copernicus Sentinel-2 data (2015-present).

## Citation
Sirko, W. et al. High-Resolution Building and Road Detection from Sentinel-2, 2023 (arXiv:2310.11622).

## How the project uses it
Heights are context only, never part of a priority level; the project carries yearly heights to 2023 and treats any later value as an estimate.
