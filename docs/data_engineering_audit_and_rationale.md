# Data Engineering Audit & Critical Architecture Rationale
## Project: TerraPulse ACUD / SpaceEye-GeoAI
**Authors:** Data & Feature Engineering Team (M2 / R2)  
**Date:** October 2026  
**Objective:** Finalize dataset boundaries, eliminate obsolete/truncated data sources, establish physical & regulatory normalization baselines, and prepare technical rationale for model development and defense.

---

## 1. Executive Problem & Business Context
* **Operational Reality:** The Administrative Capital for Urban Development (ACUD) oversees a massive land portfolio spanning hundreds of developers across residential districts (e.g., R7, R8). Manual, on-site field inspections are slow, costly, and detect construction slowdowns or developer defaults only after an acute crisis has unfolded (typically 6 to 12 months too late). This jeopardizes ACUD's land installment cash flows and damages the investment valuation of entire districts.
* **Proactive Solution:** An automated early-warning decision support system combining multi-temporal Earth Observation (satellite telemetry) with internal financial compliance indicators (Escrow accounts and land installment schedules) to predict developer distress at least 6 months before physical abandonment occurs.

---

## 2. Critical Data Auditing: Excluded Sources & Technical Rationale

Following rigorous spatial and temporal data verification, the following data channels were deliberately excluded:

### A) Exclusion of Obsolete Height Data (Google Open Buildings 2.5D Temporal)
* **Problem:** Google Open Buildings height estimates terminate at the end of **2023** and are no longer maintained. Subsequent shadow-based height extraction attempts in desert terrain exhibited unacceptable noise and error margins.
* **Decision:** **Completely drop building height as a predictive feature.** Training a model intended to operate up to 2026 on a feature that abruptly ends in 2023 introduces systematic missingness (NaNs), rendering the pipeline unviable for real-time production.

### B) Exclusion of Raw Image Semantic Segmentation
* **Problem:** Downloading terabytes of raw satellite tiles to run end-to-end semantic segmentation models (e.g., U-Net, Mask R-CNN) every 5 days incurs prohibitive compute overhead while suffering from satellite orbit drift and sun angle variations.
* **Decision:** Leverage **Zonal Statistics over fixed cadastral boundary polygons (GeoJSON)**. This aggregates spatial signals into lightweight, robust, and clean tabular time series.

### C) Exclusion of Daily Inflation & Complex Interest-Rate Curves
* **Problem:** On-site construction schedules do not respond to daily macroeconomic fluctuations; they are disrupted by **large systemic cost shocks**.
* **Decision:** Replace daily inflation indices with a discrete **Devaluation Shock Indicator (March 6, 2024 float: USD from 30.9 to 49.4 EGP)**, localized steel/cement price indices, and a binary COVID-19 disruption flag (2020–2021).

---

## 3. The Typology Ambiguity: "Villa vs. Multi-Story Apartment" Resolution

### The Ambiguity
Without structural context, models misinterpret progress:
* A 2-story standalone villa ($G+1$) reaches 100% structural completion rapidly, after which vertical growth halts. An un-normalized model risks flagging this as a stalled site.
* An 8-story residential building ($G+7$) stalling at the 2nd floor has stalled completely, despite registering the identical physical mass as the completed villa.

### Engineering Resolution: Typology-Normalized Baselines
Rather than forcing models to infer building typology blindly, we inject the masterplan zoning metadata (`typology`) as an explicit physical normalizer:

1. **Regulatory Ground Truth:** Derived directly from published ACUD masterplan terms for R7 and R8:
   * **Villa / Low-Density Parcels:** Maximum allowed height is Ground + 1 ($G+1$), with target unit density of 3 to 7 units per feddan.
   * **Apartment / High-Density Parcels:** Maximum allowed height is Ground + 7 ($G+7$), with target unit density of 35 to 70 units per feddan.
2. **Density Heuristic:** For parcels missing explicit zoning text:
   $$\text{Unit Density} = \frac{\text{Total Contracted Units}}{\text{Parcel Area (Feddans)}}$$
3. **Typology-Normalized Structural Velocity:**
   $$\text{Relative Structural Progress}_t = \frac{\text{Observed Physical Signal}_t - \text{Baseline}_{\text{sand}}}{\text{Target Saturation Level}(\text{Typology}) - \text{Baseline}_{\text{sand}}}$$
   * When a villa parcel reaches its pre-calibrated saturation threshold, the system marks structural completion as 100%.
   * When an apartment parcel stalls at that same value for consecutive quarters ($\Delta \text{Progress} = 0$) while remaining below the $G+7$ saturation threshold, the system flags a confirmed construction stall.

---

## 4. Engineering Audit: Exclusion of Radar Decibels (dB) & Raw Wavelengths

Per the team's data engineering review, **Radar Decibels (Sentinel-1 SAR C-Band backscatter in dB)** and **Raw Optical Wavelengths (uncalibrated spectral bands)** have been deliberately **excluded** from the model feature store for the following technical reasons:

1. **Desert Dielectric Penetration & SAR Noise:** In arid environments like the New Administrative Capital, dry quartz sand exhibits a very low dielectric constant ($\epsilon \approx 2.5 - 3.0$), causing C-Band radar waves (5.405 GHz) to penetrate subsurface sand layers rather than cleanly backscattering from early foundation earthworks. This produces erratic dB fluctuations ($VV$ and $VH$ shifts) that do not correlate linearly with true structural progress.
2. **Interpretability & Decision Committee Buy-In:** SpaceEye-GeoAI serves human executive decision-makers (urban planners, ACUD inspection committees, and project lenders). Features expressed in raw wavelengths ($\mu m$) or logarithmic radar decibels ($\text{dB}$) lack physical intuition. In contrast, **Physical Built Footprint Area ($m^2$)**, **Normalized Difference Built-Up Index (NDBI)**, and **Calibrated 3D Building Heights ($m$)** directly map to physical civil engineering milestones.
3. **Dimensionality & Collinearity Reduction:** Including raw band reflectances introduces severe multi-collinearity without providing additional marginal predictive power beyond NDBI and NDVI.

Therefore, the pipeline strictly standardizes on 4 discrete, human-interpretable datasets:
- **Table 1:** Parcels & Land Allocation (Acreage, Bounding Polygons)
- **Table 2:** Contractual Timelines & Typology (Launch, Handover, Target Footprint)
- **Table 3:** Optical Footprint & Urban Spectral Density (NDBI, NDVI, Footprint Ratio)
- **Table 4:** Direct 3D Building Heights & Structural Volume ($m$, $m^3$)

---

## 4. Time-Series Methodology & Stationarity Testing

The task is structured as an **Entity-Level Multi-Variate Time Series** (33 virtual twins × 45 months, from January 2023 to September 2026):

1. **Seasonality Mitigation (Seasonal Differencing):**
   * Optical desert surface reflectance exhibits periodic fluctuations in Q2 due to solar angle shifts and atmospheric dust.
   * Apply Year-over-Year (YoY) differencing to eliminate seasonal cycles:
     $$\Delta B_{12} = B_t - B_{t-4}$$
2. **Stationarity Testing (ADF Test):**
   * Cumulative construction progress curves are intrinsically non-stationary (exhibiting strong upward trends).
   * First-order differencing yields construction velocity:
     $$\text{Velocity}_t = \text{Progress}_t - \text{Progress}_{t-1}$$
   * Apply the **Augmented Dickey-Fuller (ADF) test** to ensure velocity series achieve stationarity ($p\text{-value} < 0.05$), eliminating spurious correlations.
3. **Lag Order Determination (PACF Analysis):**
   * Compute the Partial Autocorrelation Function (PACF) between Escrow liquidity drawdowns and subsequent physical construction slowdowns.
   * PACF empirically establishes the operational lag (typically a 2- to 3-month window between financial default and physical site freezing), directly informing lag-feature engineering.

---

## 5. Proposed Novel Composite KPIs

To elevate the analytical depth beyond conventional standalone metrics, we introduce three composite indicators:

1. **Reality-Reported Gap Index (RRGI):**
   $$\text{RRGI}_t = \frac{\text{Reported Progress}_t - \text{Satellite Observed Progress}_t}{\text{Reported Progress}_t}$$
   * Quantifies divergence between developer public disclosures and objective spaceborne footprint expansion, serving as an early indicator of over-reporting or misrepresentation.
2. **Financial-Physical Momentum Index (FPMI):**
   $$\text{FPMI}_t = \text{Escrow Coverage Ratio}_t \times \text{Building Growth Velocity}_t$$
   * Fuses current cash solvency with active physical velocity. A simultaneous contraction in both terms yields an early distress signal.
3. **Shock Absorption Factor (SAF):**
   $$\text{SAF} = \frac{\text{Remaining Escrow Balance}}{\text{Cost to Complete} \times \text{Material Shock Index}_{2024}}$$
   * Measures a developer's resilience against post-devaluation input cost inflation (cement and rebar price spikes following the March 2024 currency float).

---

## 6. Official Grounding & Academic References

### A) Peer-Reviewed Academic Literature:
1. **Multi-Temporal Urban Expansion via Satellite Imagery:**
   * **Paper:** Van Etten, A., et al. (2021). *"The Multi-Temporal Urban Development SpaceNet Dataset (SpaceNet 7)"*. IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR).  
   * **URL:** [https://arxiv.org/abs/2102.04420](https://arxiv.org/abs/2102.04420)
2. **Automated Built-Up Land Mapping:**
   * **Paper:** Zha, Y., Gao, J., & Ni, S. *"Use of normalized difference built-up index in automatically mapping urban areas"*. International Journal of Remote Sensing.  
   * **DOI:** [10.1080/01431160304987](https://doi.org/10.1080/01431160304987)
3. **Early Financial Distress Forecasting in Real Estate:**
   * **Journal:** *Expert Systems with Applications (Elsevier)*. Studies on hybrid ML models coupling cash-flow ratios with operational lag indicators for developer solvency prediction.

### B) Official Open Data Platforms:
* **Copernicus Data Space:** Access for Sentinel-1 SAR and Sentinel-2 L2A constellations:  
  [https://browser.dataspace.copernicus.eu/](https://browser.dataspace.copernicus.eu/)
* **Microsoft Planetary Computer:** Sentinel-2 L2A STAC catalog:  
  [https://planetarycomputer.microsoft.com/dataset/sentinel-2-l2a](https://planetarycomputer.microsoft.com/dataset/sentinel-2-l2a)
* **Google Dynamic World:** Near real-time 10m land cover classification:  
  [https://dynamicworld.app/](https://dynamicworld.app/)

### C) Egyptian Regulatory Framework & Project Codification:
* **Prime Ministerial Decree No. 2184 of 2022:** Mandates off-plan development governance in Egypt, requiring dedicated, audited project Escrow accounts and restricting developer disbursements strictly to certified engineering milestones.
* **ACUD R7 & R8 Masterplan Request for Proposal (RFP) Regulations:** Codifies maximum parcel building coverage (20%–22.5%), zoning typologies ($G+1$ villas vs. $G+7$ apartments), and contractual milestone schedules.
