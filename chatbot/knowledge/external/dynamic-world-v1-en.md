---
title: "Dynamic World V1 (Google Earth Engine dataset catalog)"
source_url: "https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1"
retrieval_date: "2026-11-02"
kind: "satellite-data"
language: "en"
notes: "Official dataset page; licence CC-BY 4.0 with required attribution."
---

# Dynamic World V1

Dynamic World is a 10 m near-real-time (NRT) Land Use/Land Cover (LULC) dataset that includes class probabilities and label information for nine classes. Predictions are available for the Sentinel-2 L1C collection from 2015-06-27 to present. The revisit frequency of Sentinel-2 is between 2 and 5 days depending on latitude. Predictions are generated for Sentinel-2 L1C images with CLOUDY_PIXEL_PERCENTAGE <= 35%, and are masked to remove clouds and cloud shadows using a combination of S2 Cloud Probability, Cloud Displacement Index and Directional Distance Transform.

All probability bands except the "label" band collectively sum to 1. To select only pixels that confidently belong to a class, the dataset page recommends masking outputs by thresholding the estimated probability of the top-1 prediction. Top-1 probabilities can be comparatively low for covers defined over time (such as crops) and for high-return surfaces in arid climates, sand or sunglint.

## Bands (pixel size 10 metres)
water, trees, grass, flooded_vegetation, crops, shrub_and_scrub, built, bare, snow_and_ice: estimated probability of complete coverage by that class (0 to 1). label: index of the band with the highest estimated probability (0 to 8; 6 = built).

## Terms of use
Licensed under CC-BY 4.0 with the attribution: "This dataset is produced for the Dynamic World Project by Google in partnership with National Geographic Society and the World Resources Institute." Contains modified Copernicus Sentinel data [2015-present].

## Citation
Brown, C.F., Brumby, S.P., Guzder-Williams, B. et al. Dynamic World, Near real-time global 10 m land use land cover mapping. Sci Data 9, 251 (2022). doi:10.1038/s41597-022-01307-4

## How the project uses it
The project reads the quarterly "built" probability per compound as the base of the activity score A (see the project specification and dataset contract).
