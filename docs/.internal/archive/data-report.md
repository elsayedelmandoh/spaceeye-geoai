# SpaceEye: Data Report for the Team

English translation of `DATA_REPORT_TEAM.md`, 25 Oct 2026.

> Paths under `real_data/` refer to the team's shared data folder (not in this repo).

## Final Data Report: Inspection Priority Observatory (SpaceEye) · R7/R8

**Final version:** 24 October 2026 · Read together with `project-plan.md` (the final plan)

> **Summary in 3 lines**
> 1. We will work on **the real districts R7 and R8: 29 named compounds** (out of 32 projects; 3 have no published name) instead of the fictional city "Horus".
> 2. Every real number we collected has **a source, a link and a quote, and an independent agent reviewed it**: 846 of 863 are valid (98%), and no number is made up.
> 3. The project has two tracks (details in `project-plan.md`): **A - Real:** we rank the real compounds by inspection priority, with no generated number at all. **B - "With your data":** the same system on virtual twins, with **only 8 generated tables**. Each table matches data that ACUD owns (escrow, installments, electricity and water, complaints...).
>
> **Usage rule:** We do not use data just because we collected it. Every table here says where it is used.

---

## 1. The origin of each piece of information (read this first)

Every column in the project has one of these types. The type must appear in the dashboard and in the presentation:

| Symbol | Type | Meaning | Example |
| --- | --- | --- | --- |
| 🟢 | **Real** | Published or observed, with a source, a link and a quote, and reviewed | Interest rate decision, satellite image, developer statement |
| 🔵 | **Derived** | We calculated it from real data with a documented method | Urban change index, area in square metres after conversion |
| 🟠 | **Generated** | Produced by the simulator for the virtual twins | Escrow account transactions, complaints |
| 🟡 | **Assumption** | A number with no published reference. It is written openly in the config file and we test its effect | Cost split across phases |
| ⚪ | **Key** | Identifier or join column | `compound_id`, `month` |

**Note:** A "developer statement" counts as 🟢 real (the statement itself is real), but it is **not an independent measurement**. We always write "the developer announced".

---

## 2. How we collected the data and checked it

1. **Collection:** 14 domains. An agent collected each domain with one rule: no number without a page that was actually opened + an exact quote + a link + a date. Broker websites are not allowed as a source for numbers. Units are kept as published.
2. **Review:** Another, independent agent reopened every source itself and tried to prove the number wrong. PDF files were downloaded again, and time series were pulled again.
3. **Verdict:** We use only the records marked `CONFIRMED` and `CONFIRMED_MINOR_FIX` in the `verification.csv` file in each folder.

| | Count |
| --- | --- |
| Facts collected | 863 |
| Valid for use | **846 (98%)** |
| Made-up or wrong numbers | **0** |
| Excluded | 17: the quote is correct but the record claimed more than the source, or the link stopped working |
| Time series | Satellites, weather, night lights, interest rate, dollar, inflation, steel and cement: 100% match with their source |

---

## 3. The big picture: where the data comes from and where it goes

```
  Real sources (government, central bank, satellites, developers, trusted news)
          │
          ▼
  Real tables  r_*  ────────────────────────────┐   (for real compounds: what we see and what was announced)
          │                                     │
          │ reference numbers + legal rules     │
          ▼                                     │
  Simulator + config files (assumptions)        │
          │                                     │
          ▼                                     │
  Generated tables  g_*  (virtual twins)  ──────┤   (the full model, including finance)
                                                ▼
         Indicators → Alerts → Dashboard → Agent that prepares the inspection file
```

**Two tracks that do not mix:**
- **Real compounds (29 named):** They get only real and derived data: images, night lights, statements, events. We put no generated financial number on them, and we never say a real developer is "distressed".
- **Virtual twins (~33 twins):** Each twin is built on the area and units of a real compound. Then the simulator generates its finance and operations. The full alert model runs here, as a demo of what the system will do with ACUD data, not as proof of accuracy.

---

## 4. Real tables used (18 tables)

| # | Table | What it contains | One row = | Size | Used in | Status |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `r_compounds` | Real compounds | Compound | 32 projects in R7/R8 (29 named) + 9 in other districts for context | A + B | Available (boundaries: 3 drawn, 6 with confirmed location, 23 to be located by the team on D1) |
| 2 | `r_developers` | Developers | Developer | ~30 | A (display only) | To be extracted |
| 3 | `r_progress_announced` | Announced progress percentages | Statement | ~25 statements for about 15 compounds + the R8 average | A (completion rule + reason sentence + backtest) + B (calibration) | Available |
| 4 | `r_project_events` | Project events | Event | ~40 | A (K3 + completion rule + backtest) | Available |
| 5 | `r_satellite_monthly` | Monthly satellite indicators | Polygon × month | 1,128 (10 compounds + 2 reference × 94 months) and will grow | Backup only (if a problem appears in Dynamic World) | Available (v2 is the approved one) |
| 6 | `r_dynamic_world_quarterly` | Built-up probability from Google Dynamic World (quarterly) | Polygon × quarter | 225 polygons × 43 quarters (2016-Q1 → 2026-Q3) | A (main measure K1/K2 + assessability K4) | Available ✅ reviewed (GO with caveats) |
| 7 | `r_sar_quarterly` | Sentinel-1 radar (height and volume), quarterly | Polygon × quarter | 10 pilot plots + 2 reference, 2016–2026 (extended to the compounds on D2) | A (K1b: vertical/volume change) | Available ✅ first test passed; independent review on D1 |
| 8 | `r_observed_stage` | Observed stage (planting, water, paved roads) | Polygon × year | Under test | A (context column + completion rule) | 🧪 Under test |
| 9 | `r_night_lights_monthly` | Monthly night lights | Zone × month | 93 months × 8 zones (January 2019 → September 2026) | A (district context) + B (occupancy calibration) | Available ✅ reviewed |
| 10 | `r_buildings_yearly` | Buildings and their height, yearly (Google Open Buildings) | Polygon × year | 223 polygons × 8 years (2016–2023) + 1 km grid | A (confirms Dynamic World + height in metres up to 2023 as context) | Available ✅ reviewed |
| 11 | `r_buildings_height_yearly` | Height of each building, yearly (Google V3 + Open Buildings) | Building × year | 43,550 buildings × 8 years (2016–2023); 32,226 inside 215 plots | A (height class of each building up to 2023: "built one floor and stopped") | Available (real) |
| 12 | `r_weather_daily` | Daily weather | Station × day | 1,392 days × 2 stations + NASA | A (dust flag) + B (temperature for electricity) | Available |
| 13 | `r_weather_events` | Announced storms and heat waves | Event | 8 storms + 7 heat waves | A ("review the scene" flag) | Available |
| 14 | `r_macro_monthly` | Monthly economy and prices | Month | 57 months (2022-01 → 2026-09) | B (2024 shock + steel and cement index); the other columns are not used | Available |
| 15 | `r_regulations` | Legal rules used | Rule | ~15 | A (K3 thresholds) + B (escrow rules) | Available |
| 16 | `r_acud_events` | ACUD enforcement events | Event | ~27 | A (problem slide) + B (~8% share) | Available |
| 17 | `r_benchmarks` | Simulation references | Parameter | ~100 (construction + land + electricity and water) | B (simulator parameters) | Available |
| 18 | `ref_calendar` | Calendar | Day | 2023–2026 | A + B | To be built |

> **(updated 25 Oct 2026)** Row 8 `r_observed_stage`: tests on 25 pilot plots (`real_data/24_surface_signals/results.md`, gate = at least 80% agreement on the test half) give these results. **Vegetation:** the Sentinel-2 NDVI vegetation share (share of pixels with NDVI > 0.2) passed with 95.5% on the test half (22 items). It covers every year, including 2026. **Paved roads:** the asphalt share from 0.3 m RGB images passed only at the edge (80.8%, 21/26), and the Sentinel-2 asphalt-like share is fragile (fit accuracy 0.67). Paved roads are therefore *supporting* evidence only, not stand-alone. **Exterior finish (paint/plaster):** failed (60%, no better than the baseline). It cannot be measured automatically and stays **visual only** in the inspection file.
>
> **(updated 25 Oct 2026)** Rows 10-11 (building height): height in metres stays limited to 2016–2023. A test that estimated height from shadows in 0.3 m images for 2024–2025 (`real_data/23_shadow_height/results.md`) **failed the gate**: plot-level MAE 5.8 m and r 0.45 (gate: MAE ≤ 4 m, r ≥ 0.80); building-level MAE 4.7 m with 46% class agreement. These shadow heights are **not used** and not published as numbers.

### What we collected and will not use

Saved and reviewed in `real_data/` in case we need it later, but it does not feed any indicator or decision:

- **Talaat Moustafa disclosures (Celia):** outside R7/R8, and the numbers are accounting liabilities, not escrow.
- **The full inflation and interest series:** from the economy we take only the March 2024 shock and the steel and cement index.
- **General market numbers** (Knight Frank for supply and deliveries, sales of the largest developers, national housing unit statistics, mortgage finance initiatives, total consumer protection complaints): these are at Cairo or Egypt level, not R7/R8. We use only: 8.5% down payment and 7.7-year installment period.
- **EOG night lights:** replaced by NASA Black Marble.
- **Sentinel-2 v1 indicators:** they have an offset error.
- **Sentinel-2 v2 indicators (NDBI, spread, NDVI):** backup only, if a problem appears in Dynamic World. They do not enter track A.
  - **(updated 25 Oct 2026)** Exception for vegetation: a plain Sentinel-2 NDVI vegetation share (NDVI > 0.2) passed the 80% gate (95.5% on the test half) and can feed the vegetation signal in `r_observed_stage`. The Dynamic World grass/trees probability did not work there (it stayed at about 0.03, which is noise).
- **Heat days as an indicator:** no rule stops construction in the heat. Temperature stays only for electricity seasonality in the simulator.
- **Sentinel-1, GHSL, WorldCover, Microsoft footprints:** they add nothing to the decision now.
- **Foreign construction references (Brazil/Sweden):** only for order of magnitude in the assumptions file.

---

## 5. Generated tables (8 tables)

Nothing has been generated yet. The simulator is built on D2 (`simulate.py`). This is the final design. The stories and the generation logic are in `project-plan.md`, section 5:

| # | Table | What it contains | One row = | Based on (real reference) | The real version is most likely held by |
| --- | --- | --- | --- | --- | --- |
| 1 | `g_twins` | Virtual twins | Twin | Area, units and district of a real reference compound; building coverage 18–22.5% (ACUD cap 22.5%), total floor area ≤ 1.6 × land | - |
| 2 | `g_plan_monthly` | Approved timeline | Twin × month | 3 years from land handover + announced dates | ACUD Planning Sector |
| 3 | `g_progress_monthly` | Progress and what the satellite sees | Twin × month | Curves fitted to announced percentages and the R8 average of 44%; DW noise calibrated on real DW | Supervising engineer reports (Art. 54) |
| 4 | `g_escrow_monthly` | Escrow, collections and cost | Twin × month | Deposit per 2184 (20/15/10/5/3%), 8.5% down payment and 7.7–12-year installments, cost per m² × steel and cement index, 2024 shock | ACUD Finance and the banks |
| 5 | `g_land_installments` | Land installments | Installment | Equal quarterly installments (ACUD since 2024); 85% facades rule | ACUD Finance |
| 6 | `g_utilities_monthly` | Electricity and water (occupancy) | Twin × month | 153 kWh/subscriber, 280–300 litres/person, household size 3.8–4.1, real temperature, official tariff tiers | Utility company |
| 7 | `g_status_events` | Warnings, grace periods and status level | Event / month | 2184 grace periods (6/12/24), ~8% late, rare termination | ACUD warning and termination records |
| 8 | `g_complaints` | Buyer complaints | Complaint | Simulator events (delay, stoppage, late reply, payment problems); the rate is a declared assumption, since no published real estate rate exists | ACUD Customer Service |

**Why the `dw_built_obs` column in `g_progress_monthly`?** The virtual twins have no real images. If we attached a real compound's images to generated finance, we would suggest that money is the cause of what appears in the images, and that is not true. So we generate "what Dynamic World would have seen" from the twin's true progress, with noise and seasonality taken from the real series.

**What was removed from the earlier design (14 tables):** Sales and costs became columns in `g_escrow_monthly`. Electricity and water are one table. The generated monitoring became a column. Generated inspections were removed (the system suggests whom to inspect, and the results of real inspections are what we ask ACUD for, to evaluate it). Tickets are created by the dashboard itself (`ops_tickets`) and are not data.

**Config files (2):**

| File | What it contains |
| --- | --- |
| `cfg_assumptions.yaml` | Every parameter: its value and its source (record_id) or an explicit "assumption": K1 threshold (0.03), inspection capacity per cycle, visit cost, simulator parameters |
| `cfg_scenarios.yaml` | The story of each twin = the answer key: healthy, gradual stall, stall after the 2024 shock, stall then recovery, finished structure with low occupancy |

**The simulator is connected, not random numbers:**

```
Cash at month end = Cash at month start + Collections + Financing − Payments
```

If the cash is not enough → contractor dues build up → construction slows down → delivery is late → complaints rise and occupancy falls (less electricity and water).

---

## 6. Column details for each table

### 6.1 Real tables

#### `r_compounds`: real compounds

One row = compound · Size: 32 projects in R7/R8 (29 named) + 9 in other districts for context · Columns: 🟢 real 9 · 🔵 derived 2

| Column | Meaning | Origin |
| --- | --- | --- |
| `compound_id` | Compound identifier | ⚪ Key |
| `name_ar / name_en` | Name | 🟢 Real |
| `developer` | Developer | 🟢 Real |
| `district` | District (R7/R8) | 🟢 Real |
| `land_area_value + unit` | Area as published (feddan/acre) | 🟢 Real |
| `land_area_m2` | Area in square metres after conversion | 🔵 Derived |
| `units_total` | Number of units | 🟢 Real |
| `launch_date` | Launch date | 🟢 Real |
| `promised_delivery` | Announced delivery date | 🟢 Real |
| `delivery_status` | Announced delivery status | 🟢 Real |
| `location_point` | Location coordinates (6 of 32 so far) | 🟢 Real |
| `boundary_polygon` | Compound boundary (drawn by the team, 3 of 32) | 🔵 Derived |
| `source_record_ids / confidence` | Source and confidence level | ⚪ Key |

#### `r_developers`: developers

One row = developer · Size: ~30 · Columns: 🟢 real 2 · 🔵 derived 2

| Column | Meaning | Origin |
| --- | --- | --- |
| `developer_id` | Developer identifier | ⚪ Key |
| `name_ar / name_en` | Name | 🟢 Real |
| `is_listed / ticker` | Listed on the stock exchange? | 🟢 Real |
| `nac_projects_count` | Number of its projects in the Capital | 🔵 Derived |
| `size_class` | Size class (small/medium/large) | 🔵 Derived |

#### `r_progress_announced`: announced progress percentages

One row = statement · Size: ~25 statements for about 15 compounds + the R8 average · Columns: 🟢 real 6

| Column | Meaning | Origin |
| --- | --- | --- |
| `compound_id` | Compound | ⚪ Key |
| `published_date` | Publication date | 🟢 Real |
| `progress_pct` | Announced percentage | 🟢 Real |
| `qualifier` | More than / about / exactly | 🟢 Real |
| `scope` | Scope of the percentage: whole project / phase / concrete | 🟢 Real |
| `stated_by` | Who made the statement (developer, consultant...) | 🟢 Real |
| `source_url` | Link | 🟢 Real |

#### `r_project_events`: project events

One row = event · Size: ~40 · Columns: 🟢 real 5

| Column | Meaning | Origin |
| --- | --- | --- |
| `compound_id` | Compound | ⚪ Key |
| `event_type` | Launch / delivery start / delivery complete / postponement | 🟢 Real |
| `event_date` | Event date (if stated) | 🟢 Real |
| `published_date` | Publication date | 🟢 Real |
| `value + unit` | Related value (for example 1,084 units) | 🟢 Real |
| `source_url` | Link | 🟢 Real |

#### `r_satellite_monthly`: monthly satellite indicators

One row = polygon × month · Size: 1,128 (10 compounds + 2 reference × 94 months) and will grow · Columns: 🟢 real 3 · 🔵 derived 4

| Column | Meaning | Origin |
| --- | --- | --- |
| `polygon_id / compound_id` | Polygon and compound | ⚪ Key |
| `month / scene_id` | Month and the scene used | 🟢 Real |
| `valid_frac` | Share of valid pixels after the cloud mask | 🟢 Real |
| `ndvi_median` | Vegetation index | 🔵 Derived |
| `ndbi_median` | Raw built-up index | 🔵 Derived |
| `ndbi_spread` | Spread of values inside the compound (p90−p10): the main measure | 🔵 Derived |
| `spread_minus_ref` | Spread minus the reference desert | 🔵 Derived |
| `dust_flag` | Is the day a dust day (from weather data) | 🟢 Real |

#### `r_dynamic_world_quarterly`: built-up probability from Google Dynamic World (quarterly)

One row = polygon × quarter · Size: 225 polygons × 43 quarters (2016-Q1 → 2026-Q3) · Columns: 🟢 real 3 · 🔵 derived 1

| Column | Meaning | Origin |
| --- | --- | --- |
| `polygon_id / compound_id` | Polygon and compound | ⚪ Key |
| `quarter` | Quarter | ⚪ Key |
| `built_prob_mean` | Mean built-up probability: the basis of K1/K2 | 🟢 Real |
| `built_label_share` | Share of pixels labelled "built" | 🟢 Real |
| `n_images` | Number of images used | 🟢 Real |
| `delta_b12` | Year-over-year change ΔB₁₂ (K1), threshold 0.03 | 🔵 Derived |

#### `r_sar_quarterly`: Sentinel-1 radar (height and volume), quarterly

One row = polygon × quarter · Size: 10 pilot plots + 2 reference, 2016–2026 (extended to the compounds on D2) · Columns: 🟢 real 2 · 🔵 derived 1

| Column | Meaning | Origin |
| --- | --- | --- |
| `polygon_id / quarter` | Polygon and quarter | ⚪ Key |
| `vv_db / vh_db` | Radar signal in decibels (rises with construction and height) | 🟢 Real |
| `n_scenes` | Number of scenes used | 🟢 Real |
| `delta_vv12` | Year-over-year change ΔVV₁₂ (K1b), threshold 0.5 dB | 🔵 Derived |

#### `r_observed_stage`: observed stage (planting, water, paved roads)

One row = polygon × year · Size: under test · Columns: 🟢 real 2 · 🔵 derived 2

| Column | Meaning | Origin |
| --- | --- | --- |
| `polygon_id / year` | Polygon and year | ⚪ Key |
| `dw_grass_trees` | Planting/grass probability from Dynamic World | 🟢 Real |
| `dw_water` | Water probability (pools/lakes) | 🟢 Real |
| `paved_frac` | Share of paved (asphalt) roads from Sentinel-2 | 🔵 Derived |
| `observed_stage` | Stage: foundations / construction / stalled structure / exterior works / complete | 🔵 Derived |

> **(updated 25 Oct 2026)** Test results (`real_data/24_surface_signals/results.md`, 25 pilot plots, gate ≥ 80% on the test half):
> - **Vegetation:** `dw_grass_trees` did not work; it stayed at about 0.03 (noise). A plain Sentinel-2 NDVI vegetation share (NDVI > 0.2) **passed** with 95.5% on the test half (22 items). Plot values go from 0 to 0.3–0.5 as compounds are landscaped, and it covers 2026 (Jun–Sep). Vegetation from RGB excess-green failed (50%).
> - **Paved roads (`paved_frac`):** RGB asphalt share 80.8% (passes barely); Sentinel-2 asphalt-like share 90.9% on test but only 0.67 on the fit half (fragile threshold; it also picks up building shadows and dark roofs). Use as **supporting** evidence only, not stand-alone.
> - **Exterior finish (paint/plaster):** **failed** (60%, same as the majority baseline). It cannot be measured automatically from these images and stays **visual only** in the inspection file.
> - Caveats: a single rater with no second labeller, no ground visit, small test half (22–26 items).

#### `r_night_lights_monthly`: monthly night lights

One row = zone × month · Size: 93 months × 8 zones (January 2019 → September 2026) · Columns: 🟢 real 4

| Column | Meaning | Origin |
| --- | --- | --- |
| `zone_id` | Zone | ⚪ Key |
| `month` | Month | 🟢 Real |
| `product` | EOG or NASA Black Marble | 🟢 Real |
| `radiance_mean / median / p90` | Light intensity | 🟢 Real |
| `valid_obs` | Number of valid observations | 🟢 Real |

#### `r_buildings_yearly`: buildings and their height, yearly (Google Open Buildings)

One row = polygon × year · Size: 223 polygons × 8 years (2016–2023) + 1 km grid · Columns: 🟢 real 3

| Column | Meaning | Origin |
| --- | --- | --- |
| `polygon_id` | Polygon | ⚪ Key |
| `year` | Year | 🟢 Real |
| `building_presence_frac` | Share of built-up area | 🟢 Real |
| `mean_height_m` | Mean building height | 🟢 Real |

#### `r_buildings_height_yearly`: height of each building, yearly (Google V3 + Open Buildings)

One row = building × year · Size: 43,550 buildings × 8 years (2016–2023); 32,226 inside 215 plots · Columns: 🟢 real 2 · 🔵 derived 1

| Column | Meaning | Origin |
| --- | --- | --- |
| `building_id / plot_id / year` | Building, plot and year | ⚪ Key |
| `height_m` | Mean observed height | 🟢 Real |
| `presence` | Probability that the building exists | 🟢 Real |
| `class` | None / low 3–8 m / partial 8–20 m / full ≥20 m | 🔵 Derived |

> **(updated 25 Oct 2026)** There is still no height in metres after 2023. Height from shadows in 0.3 m images (2024–2025) was tested and **failed the gate** (`real_data/23_shadow_height/results.md`): plot level MAE 5.8 m, r 0.45 (gate: MAE ≤ 4 m, r ≥ 0.80); building level MAE 4.7 m, class agreement 46% (gate ≥ 75%). It is **not used**, and the heights are not published as numbers.

#### `r_weather_daily`: daily weather

One row = station × day · Size: 1,392 days × 2 stations + NASA · Columns: 🟢 real 4 · 🔵 derived 2

| Column | Meaning | Origin |
| --- | --- | --- |
| `station / date` | Station and day | ⚪ Key |
| `max_temp_c` | Maximum temperature | 🟢 Real |
| `min_visibility_m` | Minimum visibility | 🟢 Real |
| `max_wind_kt` | Maximum wind | 🟢 Real |
| `dust_flag / severe_dust_flag` | Dust day / severe dust | 🔵 Derived |
| `t2m_max_power` | Maximum temperature from NASA POWER | 🟢 Real |
| `heat_day_40` | Hot day ≥ 40° | 🔵 Derived |

#### `r_weather_events`: announced storms and heat waves

One row = event · Size: 8 storms + 7 heat waves · Columns: 🟢 real 3 · 🔵 derived 1

| Column | Meaning | Origin |
| --- | --- | --- |
| `event_date` | Date | 🟢 Real |
| `event_type` | Dust storm / heat wave | 🟢 Real |
| `metar_confirmed` | Did the airport confirm it | 🔵 Derived |
| `source_url` | Link | 🟢 Real |

#### `r_macro_monthly`: monthly economy and prices

One row = month · Size: 57 months (2022-01 → 2026-09) · Columns: 🟢 real 5 · 🔵 derived 1

| Column | Meaning | Origin |
| --- | --- | --- |
| `month` | Month | ⚪ Key |
| `policy_rate` | Interest rate | 🟢 Real |
| `usd_egp_avg` | Average dollar exchange rate | 🟢 Real |
| `inflation_yoy` | Annual inflation | 🟢 Real |
| `steel_ton_egp` | Price per ton of steel (indicative) | 🟢 Real |
| `cement_ton_egp` | Price per ton of cement | 🟢 Real |
| `shock_flag` | Shock month flag (for example March 2024) | 🔵 Derived |

#### `r_regulations`: legal rules used

One row = rule · Size: ~15 · Columns: 🟢 real 4

| Column | Meaning | Origin |
| --- | --- | --- |
| `rule_id` | Identifier | ⚪ Key |
| `instrument / article` | Decree and article (for example 2184/2022 Art. 3) | 🟢 Real |
| `parameter` | Parameter (deposit share, delivery grace period...) | 🟢 Real |
| `value + unit` | Value | 🟢 Real |
| `source_url` | Link | 🟢 Real |

#### `r_acud_events`: ACUD enforcement events

One row = event · Size: ~27 · Columns: 🟢 real 5

| Column | Meaning | Origin |
| --- | --- | --- |
| `event_date` | Date | 🟢 Real |
| `event_type` | Grace period / rescheduling / termination / statement | 🟢 Real |
| `value` | Value (for example 7–8%) | 🟢 Real |
| `stated_by` | The body that stated it | 🟢 Real |
| `source_url` | Link | 🟢 Real |

#### `r_benchmarks`: simulation references

One row = parameter · Size: ~100 (construction + land + electricity and water) · Columns: 🟢 real 2

| Column | Meaning | Origin |
| --- | --- | --- |
| `parameter` | Parameter (land price, cost per m², building coverage...) | ⚪ Key |
| `value_low / value_high` | Range | 🟢 Real |
| `unit / year` | Unit and year | 🟢 Real |
| `confidence / record_ids` | Confidence and source | ⚪ Key |

#### `ref_calendar`: calendar

One row = day · Size: 2023–2026 · Columns: 🟢 real 2 · 🔵 derived 1

| Column | Meaning | Origin |
| --- | --- | --- |
| `date` | Day | ⚪ Key |
| `ramadan_flag / holiday_flag` | Ramadan and holidays | 🟢 Real |
| `dst_flag` | Daylight saving time | 🟢 Real |
| `season` | Season | 🔵 Derived |

### 6.2 Generated tables

> **(updated 25 Oct 2026)** The full generator design and the final schemas are in `synthetic-data-plan.md` (section 10), which supersedes the columns below where they differ. Main changes: hidden truth (true progress, story, true occupancy, the model label and each complaint's true cause) moves to `answer_key.csv`; the horizon is 45 months (Jan 2023 to Sep 2026).

#### `g_twins`: virtual twins

One row = twin · Size: ~33 · Columns: 🟢 real 1 · 🟡 assumption 1 · 🔵 derived 1 · 🟠 generated 2

| Column | Meaning | Origin |
| --- | --- | --- |
| `twin_id` | Twin identifier | ⚪ Key |
| `template_compound_id` | The real reference compound | ⚪ Key |
| `district / land_area_m2 / units_total` | From the reference compound | 🟢 Real |
| `building_coverage_pct` | Building coverage, 18–22.5% (ACUD cap 22.5%) | 🟡 Assumption |
| `floors` | Floors, 5–8 (cap ground + 7) | 🟡 Assumption |
| `bua_m2` | Built-up area = land × min(coverage × floors, 1.6) | 🔵 Derived |
| `land_handover_date` | Land handover | 🟠 Generated |
| `contractual_delivery_date` | Contractual delivery date (the story itself is in `answer_key.csv`) | 🟠 Generated |

#### `g_plan_monthly`: approved timeline

One row = twin × month · Size: ~33 × 45 · Columns: 🟠 generated 2

| Column | Meaning | Origin |
| --- | --- | --- |
| `twin_id / month` | Twin and month | ⚪ Key |
| `planned_progress_pct` | Planned progress | 🟠 Generated |

#### `g_progress_monthly`: progress and what the satellite sees

One row = twin × month · Size: ~33 × 45 · Columns: 🟠 generated 3 · 🔵 derived 1

| Column | Meaning | Origin |
| --- | --- | --- |
| `twin_id / month` | Twin and month | ⚪ Key |
| `reported_progress_pct` | Progress as reported by the supervising engineer (quarterly, rounded, can be biased or missing); true progress is in `answer_key.csv` | 🟠 Generated |
| `facades_pct` | Facades progress (for the 85% rule) | 🟠 Generated |
| `dw_built_obs` | Built-up probability as Dynamic World would see it | 🟠 Generated |
| `stall_flag` | Work stoppage | 🔵 Derived |

> **(updated 25 Oct 2026)** On real compounds, exterior finish (paint/plaster) cannot be measured from satellite images (test failed at 60%, `real_data/24_surface_signals/results.md`). So `facades_pct` has no observed counterpart; on real compounds, finish stays visual only in the inspection file.

#### `g_escrow_monthly`: escrow, collections and cost

One row = twin × month · Size: ~33 × 45 · Columns: 🟠 generated 3 · 🟢 real 2 · 🔵 derived 1

| Column | Meaning | Origin |
| --- | --- | --- |
| `twin_id / month` | Twin and month | ⚪ Key |
| `units_sold / collections` | Units sold and collections | 🟠 Generated |
| `deposits / withdrawals / balance` | Escrow transactions and balance | 🟠 Generated |
| `required_min_pct` | Minimum required by decree 2184 | 🟢 Real |
| `cost_to_complete` | Remaining cost | 🟠 Generated |
| `material_cost_index` | Steel and cement index | 🟢 Real |
| `coverage_ratio` | Balance ÷ remaining cost (TP-03) | 🔵 Derived |

#### `g_land_installments`: land installments

One row = installment · Size: ~33 × 16 · Columns: 🟠 generated 2 · 🔵 derived 1

| Column | Meaning | Origin |
| --- | --- | --- |
| `twin_id / installment_no` | Twin and installment number | ⚪ Key |
| `due_date / amount` | Due date and amount | 🟠 Generated |
| `paid_date / paid` | Payment | 🟠 Generated |
| `months_late` | Delay in months | 🔵 Derived |

#### `g_utilities_monthly`: electricity and water (occupancy)

One row = twin × month · Size: ~33 × 45 · Columns: 🟠 generated 3 · 🟢 real 1 · 🔵 derived 1

| Column | Meaning | Origin |
| --- | --- | --- |
| `twin_id / month` | Twin and month | ⚪ Key |
| `meters_active` | Active residential meters (true occupancy is in `answer_key.csv`) | 🟠 Generated |
| `kwh` | Electricity consumption | 🟠 Generated |
| `m3` | Water consumption | 🟠 Generated |
| `t2m_max_mean` | Temperature (air conditioning seasonality) | 🟢 Real |
| `occupancy_gap` | Built but no consumption | 🔵 Derived |

#### `g_status_events`: warnings, grace periods and status level

One row = event / month · Size: depends on the stories · Columns: 🟠 generated 1 · 🔵 derived 2

| Column | Meaning | Origin |
| --- | --- | --- |
| `twin_id / date` | Twin and date | ⚪ Key |
| `event_type` | Warning / grace period / termination | 🟠 Generated |
| `status_level` | The five-level status | 🔵 Derived |

#### `g_complaints`: buyer complaints

One row = complaint · Size: a few thousand (Arabic text for a sample only) · Columns: 🟠 generated 4 · 🔵 derived 2

| Column | Meaning | Origin |
| --- | --- | --- |
| `complaint_id / twin_id / date` | Complaint, twin and date | ⚪ Key |
| `channel` | Channel (phone, portal, visit) | 🟠 Generated |
| `category` | Category: delay / work stoppage / payment and installments / quality / other | 🟠 Generated |
| `text_ar` | Complaint text in Arabic (sample only, no personal data) | 🟠 Generated |
| `category_llm` | Category from the language model (to demo the classifier) | 🔵 Derived |
| `complaints_per_1000_units` | Complaints per 1,000 units per month (TP-04) | 🔵 Derived |

---

## 7. Definition of distress (5 levels, for track B only)

**In track A (real) we do not use the word "distressed".** We use K2 "quarters with no observed change" and K3 "months after the announced delivery date". The levels below apply to the virtual twins only (`g_status_events`):

| Level | When | Reference |
| --- | --- | --- |
| 🟢 On plan | Progress is close to plan, and the pace is normal | Execution schedule |
| 🟡 Behind plan | Progress is well below plan, or the pace has dropped, before the delivery date | Execution schedule |
| 🟠 Late on delivery | Passed the delivery date, and still inside the 12-month grace period | Decree 2184/2022 Art. 5 |
| 🔴 Distressed | Any of: more than 24 months after the delivery date (right to a refund) · **no progress for 6 months in a row** (the status regularization period in the decree) · ongoing land installment arrears with insufficient escrow | Decree 2184 + ACUD practice |
| ⚫ Terminated | ACUD terminated the contract (by mutual agreement or otherwise) | ACUD statement about 6 cases |

- **What the model predicts:** "Will the compound reach level 🔴 within the next 6 months?" It is calculated every 3 months, in line with ACUD's review cycle.
- **Shares in the simulation:** about 8% become late/distressed (ACUD statement), and termination is a much smaller share (🟡 assumption, because we know the number of cases but not out of what total).
- **On real compounds** we only say "no observed progress for 6 months". We do not say "distressed".

---

## 8. Key real values the design depends on

| Value | Source |
| --- | --- |
| Escrow deposit **20/15/10/5/3%** of construction cost by area class; 12-month delivery grace period; refund after 24 months; 6-month status regularization period | Prime Minister's Decree 2184/2022 (Cabinet portal) |
| Progress reports every 3 months from the supervising engineer (Art. 54), and the building occupancy certificate (Art. 62) | Building Law 119/2008 |
| 7–8% of developers are seriously late, mutual termination for 6, field review every 3 months | Statements by the ACUD chairman (September–October 2026) |
| Building conditions for developer plots: ground floor **≤ 22.5%** of the plot, apartments ground + 7, villas ground + 1, **average occupancy factor 1.6** (total floor area ÷ land), basement allowed, services 8–12% of land. Developer designs announced at 18% (Moraya) and 22.5% (LA REVA). The binding value per plot is in its allocation contract (data request) | ACUD 2018 building conditions (Masrawy, 3 Feb 2018, RFP-0002) + developer statements (RFP-0008, R8-0072) |
| Land installments: equal quarterly installments (since January 2024); detailed R8 terms not confirmed | Masrawy, Amwal Al Ghad |
| Liquidity shock: the 6 March 2024 float. The dollar went from 30.94 to 49.44, the interest rate +600 basis points to 27.25% | Central Bank of Egypt |
| 8.5% down payment and 7.7-year installment period on average (Greater Cairo) | Knight Frank Q1 2025 |
| Construction cost 720–1,270 USD/m²; ACUD land price from ~2,500 to 10–12 thousand EGP/m² | Knight Frank; ACUD chairman |
| Average progress of all of R8 is 44% (June 2025) | Etqan study (Daily News Egypt) |
| Dynamic World matches Open Buildings: median correlation 0.95 on plots ≥ 2 hectares, 2016–2023; year-over-year change noise 0.01–0.03 | Our calculation on two Google sources, independently reviewed (Brown et al. 2022, CC BY 4.0) |
| The built-up area within the Capital's boundary grew about 9 times between 2016 and 2023 (area numbers are approximate), and the mean height went from ~14 to ~18.5 m: an independent yearly reference to calibrate the satellite indicator | Google Open Buildings 2.5D Temporal (CC BY 4.0) |
| Electricity use: ~153 kWh/month per residential subscriber (Egypt average, 2023/24); summer peak June–August | Annual report of the Egyptian Electricity Holding Company (calculated from it) |
| Electricity tariff tiers: 0.68 → 2.23 EGP/kWh (August 2024), and 0.68 → 2.89 (from the August 2026 bill) | Enterprise + the annual report; Al-Dostour and Banker |
| Water: 280–300 litres/person/day in new cities (200 in cities in general); tariff tiers 2–4.5 EGP/m³ (low confidence, one news source) | Holding Company for Water and Wastewater as published; Banker News |
| Household size: 3.8 urban, 4.1 overall | Demographic and Health Survey 2014, Household Income, Expenditure and Consumption Survey 2019/20 |

> **(updated 25 Oct 2026)** The height reference above ends in 2023. A shadow-based height estimate for 2024–2025 failed the gate (plot MAE 5.8 m, r 0.45) and is not used (`real_data/23_shadow_height/results.md`).

---

## 9. What changed from the specs file (01-specs.md)

| Point | Before | Now |
| --- | --- | --- |
| Deposit shares | 10–30% ❌ wrong | 20/15/10/5/3% |
| Progress indicator TP-01 | Higher NDBI = more construction ❌ | Spread of values inside the compound, compared with itself in the same season, minus the reference desert. Its name is "observed urban change" |
| Weather | Exclude dust and heat days | "Review the image" flag + context; no official decision stops construction in the heat |
| Compounds | 33 fictional | 32 real (track A) + ~33 virtual twins (track B) |
| Product | "Distress Radar" | "Inspection Priority Observatory": real ranking + "With your data" demo |
| Main urban change indicator | NDBI | Google Dynamic World (quarterly up to 2026), checked against Open Buildings |
| Generated tables | ~7 in the specs, then 14 in the first design | 7 tables, each matching data held by ACUD |
| Occupancy | Generated electricity and water only | Real night lights (observed) + generated electricity and water based on real references |
| Distress | "Stoppage within 8–12 weeks" | 5 levels from decree 2184 and ACUD practice; the target: distress within 6 months |
| Liquidity shock | Example numbers | The March 2024 float and real steel and cement prices |

---

## 10. Wording rules (on slides and in the dashboard)

| ❌ We do not say | ✅ We say |
| --- | --- |
| "Progress is 70%" | "The developer announced 70%" + the date + the scope (project/phase/concrete) |
| "ACUD reviews all projects every 3 months" | "According to the ACUD chairman's statement" |
| "10–12 companies are distressed" | "Those seriously late are no more than about 7–8%" |
| "Celia escrow balance" | "An accounting liability published in the financial statements" |
| "The official building coverage is 20%" | "ACUD caps the ground floor at 22.5% (2018 conditions); announced designs 18–22.5%" |
| "The market price of steel" | "The indicative price in the ministry's bulletin" |
| "The new developers law" | "A draft under discussion" |
| "We proved that dust distorts the images" | "A weak indicator; we add a review flag" |

---

## 11. Current status

| Item | Status |
| --- | --- |
| NASA Black Marble night lights | ✅ 93 full months (2019 → September 2026). This is the approved series (not merged with EOG). Residential districts keep rising. A drop in the Government District zone since April 2026 is not explained yet. ✅ Reviewed (recalculation matches) |
| Google Open Buildings (buildings and their height 2016–2023) | ✅ Pulled without calculation: 223 polygons × 8 years. Example: pilot compound 819189945 went from 1% built (2019) to 18% (2021). ✅ Reviewed (recalculation matches) |
| Electricity and water references | ✅ Collected and reviewed (55 of 55 valid) |
| Google Dynamic World (quarterly built-up probability 2016 → 2026-Q3) | ✅ 225 plots. **Independent review: GO with caveats.** 36 values were recalculated and matched; the correlation with Open Buildings has a median of 0.95 on plots ≥ 2 hectares. Compare year to year only (seasonal); we use `built_prob_mean`; noise 0.01–0.03; 2024–2026 have no independent reference after 2023 |
| Compound boundaries | 3 drawn and 6 with a confirmed location. **The team on D1 must locate 23 named compounds** on Google Maps or the developer's map (one or two minutes per compound). 3 projects with no published name are excluded unless identified |
| ACUD tender conditions booklet (acud.eg/rfp) | The website is down; it is on the data request list |

> **(updated 25 Oct 2026)** Surface signals and post-2023 height (tested on pilot plots):
> - Vegetation: Sentinel-2 NDVI vegetation share ✅ passed (95.5% on the test half; gate 80%). `real_data/24_surface_signals/results.md`
> - Paved roads: 80.8% (RGB), supporting evidence only. Same file.
> - Exterior finish: ❌ failed (60%), visual only in the inspection file. Same file.
> - Building height from shadows, 2024–2025: ❌ failed the gate (plot MAE 5.8 m, r 0.45); not used. So Dynamic World 2024–2026 still has no independent height reference after 2023. `real_data/23_shadow_height/results.md`

---

## 12. What we will ask ACUD for (the last slide in the presentation)

Every 🟠 generated table matches a real source inside ACUD. When that source comes in, it replaces the generated one:

1. Plot boundaries and the developer of each plot → `boundary_polygon` (replaces the team's drawing)
2. The approved timeline and contractual delivery dates → `g_plan_monthly`
3. Quarterly supervising engineer reports → `g_progress_monthly`
4. The field review log and its results → the ground truth to evaluate the ranking
5. The log of warnings, grace periods and terminations → `g_status_events`
6. Land installments and arrears → `g_land_installments`
7. Escrow account balances and collections → `g_escrow_monthly`
8. Meter requests, occupancy certificates and consumption readings → `g_utilities_monthly`
9. R7 and R8 tender conditions booklets → building coverage in `g_twins`
10. Anonymised buyer complaints → `g_complaints`

---

## 13. Where the files are

All real data is in `Project/real_data/`. Each folder has: `records.csv` (the fact + the quote + the link), `verification.csv` (the review verdict), `raw/` and `scripts/`.

| Folder | Contents |
| --- | --- |
| `01_nac_city` | Facts about the Capital and ACUD |
| `02_regulation_enforcement` | Decree 2184 and ACUD enforcement events |
| `03_projects_R7` · `04_projects_R8_other` | Compound register, progress percentages and events |
| `05_geo_satellite` | OSM and Sentinel-2 images. **`sentinel_indices_v2.csv` is the approved one** (v1 has an error) |
| `06_weather_dust` | Weather, dust and heat |
| `07_macro_prices` | Interest rate, dollar, inflation, steel and cement |
| `08_developer_disclosures` | Talaat Moustafa and Palm Hills disclosures |
| `09_laws_regulations` | Building, consumer, contractor, data and labour laws |
| `10_market_complaints` | Market and aggregated complaints |
| `11_occupancy_infrastructure` | Night lights and occupancy |
| `12_simulation_benchmarks` | Simulation references |
| `13_acud_rfp_conditions` | Building requirements and tender conditions |
| `14_open_buildings_temporal` | Buildings and their height, yearly 2016–2023 (Google) |
| `15_compound_boundaries` | Compound boundaries and locations |
| `16_utility_benchmarks` | Electricity and water references |
| `17_builtup_2024_2026_options` | Google Dynamic World quarterly 2016–2026 and other options (Sentinel-1, Esri Wayback) |

The detailed report with all sources and links: `Project/real_data/DATA_REPORT_AR.md`
