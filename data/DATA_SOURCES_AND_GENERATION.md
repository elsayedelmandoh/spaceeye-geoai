# Data sources and generation logic

Scope: the current R7 ready-data bundle,including component inputs. This document describes the implemented code,not a claim that every external page was re-opened today. The source registry keeps recorded audit decisions and publication dates. No project-specific synthetic value becomes verified merely because a related news item exists.

## Files that provide the trace

- `SOURCE_CATALOG.csv`: coded published-statement sources plus background audit references,with source IDs,dates,recorded decisions and safe URLs. `scope` distinguishes current statement evidence from broader background references. Unsafe project-name URLs are withheld explicitly,not disguised.
- `SOURCE_INPUTS.csv`: configured source/cache file paths and SHA-256 values. These are provenance records,not bundled raw inputs.
- `GENERATION_PARAMETERS.json`: exact current seed,thresholds,financial/synthetic assumptions and generator settings.
- `configs/synthetic_sources.json`: context supporting land-price/relief assumptions,and exactly what those sources do not establish.
- Bundle `PROVENANCE.json`,`MANIFEST.csv` and `docs/component_validation.json`: copied-table hashes,package hashes and component checks.

Original source quotes and code/name mapping remain in the controlled external source register. The ready bundle does not distribute them. See per-table column dictionaries for field types/origins.

## Public and derived inputs

| Data | Source family | How it enters the implemented tables |
| --- | --- | --- |
| Compound register and public promises/progress/events | Reviewed public statements and accepted coded fact records;IDs link to SOURCE_CATALOG | Public dates/values are retained as published. Missing register sizes/units/floors use declared generated assumptions with adjacent origin fields. A statement is evidence of what was announced,not an independently surveyed completion measurement. |
| Working boundary polygons | Reviewed location files and image/map alignment;OpenStreetMap is a reference input | Polygons are coded and confidence-filtered. They are team working geometries,not legal survey boundaries. Real-estate/broker maps are location aids only,not sources for numerical contract claims. |
| Built probability and land-cover shares | Google Dynamic World cached imagery products | Compound-quarter aggregation,quality/image-count checks and twelve-month land-cover shares. K1compares the last4quarters with the previous4. It is built probability,not measured built area. |
| Activity score | Dynamic World/Sentinel-2window features with Open Buildings plot labels | Existing trained gradient-boosting activity model;accepted q2holdmode carries the latestQ2window until the next one. Quarterly rows are not independent fresh activity observations every quarter. No model was retrained to produce the component bundle. |
| Vegetation | Sentinel-2summer imagery | NDVI-based vegetation share;computed product,not a field landscape survey. |
| Height | Google Open Buildings temporal product through2023;approved localv4built-mask estimate for2024 | Origins are retained. Later experimental height/finishing products were not approved and are not substituted. No per-building surveying guarantee is claimed. |
| Exchange rate and interest rate | Audited Central Bank of Egypt macro series | USD/EGPmonthly average and deposit policy rate are copied from the coded reference table. |
| Rebar/cement | Audited building-material bulletin series | Indicative EGP/tonne values. Materials index is the mean of rebar/cement ratios to their first month,times100. It is not an individual contractor invoice. |
| Temperature and hot days | NASA POWER MERRA-2grid cell30.02N,31.75E | Monthly aggregation of the reference weather series. This is model-grid weather,not an on-site instrument. IEM METAR airport dust records also exist in the wider audit,but dust fields do not enter the current drivers table. |
| Calendar | Configured Ramadan/Eid intervals | Calendar-day overlap per month;declared date ranges,not inferred construction shutdowns. |
| Rules | Audited canonical Decree2184/2022,Law119/2008 and recorded building-condition references | Values are represented in the versioned rules table. They do not establish individual fine eligibility or replace allocation contracts. |

Dataset/service references: [Dynamic World](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1),[Sentinel-2](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED),[Open Buildings](https://sites.research.google/open-buildings/),[NASA POWER](https://power.larc.nasa.gov/),[IEM METAR](https://mesonet.agron.iastate.edu/request/download.phtml),[OpenStreetMap Overpass](https://overpass-api.de/api/interpreter). These identify products/services;project observations come from the cached,audited inputs listed in SOURCE_INPUTS.

## How indicators are derived

- K2counts consecutive inactive quarters after the legacy start rule. A published launch can trigger that legacy state;it is not a pure physical-start measurement.
- Observed start requires four consecutive assessable active quarters or already-published delivery. K6counts time from the first known launch/promise-publication reference without confirmed observed start;missing evidence remains unknown. K6above24months adds priority1;13–24adds priority2.
- K3uses the first published delivery promise. Later promises do not reset its clock. Only facts published by the cutoff enter a context.
- K5unions post-deadline/no-start and post12-month-grace months,subtracting overlap. Accrual stops at published handover,previous exposure remains. This is a research-policy screening proxy,not assessed contract fines.
- Inspection capacity4is one third of12. Only eligible priorities1–3are selected,ordered by level,K2descending,K3descending,code. Capacity2/6comparisons change selection only.

## Historical operations: what is generated and why

All internal company operations are synthetic stand-ins because actual internal registers are unavailable. Seed2026and per-entity RNGstreams make the outputs repeatable. The model never learns hidden truth as an input.

| Generated part | Method and links to the rest of the data |
| --- | --- |
| Developer traits and project story | Derived story categories follow public activity/event patterns;financial strength and reporting style are generated. Stories bias plausible operations,not measured developer behavior. |
| Contractual plan | Weibull S-curve with configured duration/shape and an announced deadline where available. This is an assumed schedule shape;no yearly construction S-curve is inferred from legislation. |
| Historical physical progress | Reconstructed monotone path through public-announcement/known-handover anchors,with seasonal weights and correlated noise. Finishing remains uncertain. This is an anchored reconstruction,not evidence that cash causally generated the actual history. |
| Cost | BUAand generated USD/m2cost scale,combined with exchange-rate/material drivers and declared imported share. Remaining cost follows generated/report progress. It is not actual developer cost disclosure. |
| Sales/prices/collections | Launch-and-tail sales process,remaining saleable units,rate/calendar effects,post-float price assumptions,down payment and installment schedules. Units_soldis a MONTHLYflow,not cumulative inventory. |
| Cash,coverage,debt and installments | Generated collections/releases,costs,finite assumptions and funding behavior conditional on the reconstruction. Financial guarantees are distinguished from liquid operating cash. Land dues use16quarterly installments;historical land-price draws retain their original configured range. |
| Supervisor reports | Imperfect observations of generated progress:quarterly arrival,delay,rounding,optimism and missingness. Published announcement months follow their source anchor. |
| Meters,consumption and roads | Generated handover/occupancy relationships,temperature seasonality and paving assumptions. Electricity only;no actual water-meter or paved-road timing product is supplied. |
| Complaints | Counts respond to generated sold inventory and events;desk labels can be wrong,texts include spelling variation/mixed topics,channels and occasional repeats. Text is synthetic Arabic,not copied personal complaints. |
| Administrative status/warnings | Generated review observations under declared policy rules. They are excluded from model X and do not establish real company distress. |

The raw simulation intentionally contains defects. The ready bundle uses the cleaned copy:monthly duplicates removed,detected thousand-EGPbalances repaired,invalid report observations suppressed,unknown-code complaints quarantined and phones masked. Rejected/raw rows are not included. Public launch gaps still prevent independently verifying every pre-launch complaint.

## Generated missing contract inputs and fine amounts

Synthetic allocation is6–18months before the earliest public/observed anchor,bounded by2016-01-01. This lag is an explicit assumption,not a published statistic. Because dates are retrospectively constrained,they are excluded from X/public K6.

Fallback land-price envelopes are2500–5000EGP/m2before2023and5000–12000otherwise. They are interpolation assumptions informed by old/new offer-price context,not individual contract prices. Available generated positive installments take precedence:median installment times16provides the quarterly land-value estimate without reading future dues.

`K5_egp = K5_months * assumed_land_value_egp * 0.005`. The 0.5% monthly rate (owner decision, 3 November 2026; was 1%) is illustrative and not established by the news. The EGPfield is not deducted from historical/forward cash ledgers. Optional50%relief and12-month scheduling are separate cases gated at18November2024,with no universal eligibility or known permanent expiry claimed.

Context references: [land-offer price reporting](https://banker.news/155071),[relief reporting](https://hapijournal.com/2024/11/18/خفض-غرامات-التنفيذ-50-العاصمة-الإدارية/),[contract-dependent enforcement reporting](https://www.cairo24.com/879515). The exact sampled dates/rates remain generated. Sources do not identify a coded project's private contract.

## Forward financial paths and hypothetical review priorities

The separate engine starts at2025-03with available reports and finance only. It compares baseline,collections−25%for6months,and30%FXimpact on the declared40%imported share,using the same initial state/productivity draws. Assumed working capital and finite credit constrain spending,then spending constrains progress. No future handover,private true progress or hidden rescue is used to force an outcome.

The new priority extension freezes cutoff public context and observed B1/B2/B3financial flags. Projected plan is cutoff planned_pctplus declared monthly capacity times elapsed months,capped100. B5fires when projected plan minus simulated progress exceeds20percentage points. Existing B1+K2rule,completion cap and capacity4remain. Each month is compared with that month's baseline. These648rows are hypothetical rule outputs,not forecasts of future satellite activity or validated priority accuracy.

## Complaint training data

The100masked feed texts are joined to existing generated category truth ONLYto create label_category and conservative duplicate/template groups. text_aris the sole X. Desk categories are noisy and excluded. Connected shared body templates/duplicate families cannot cross the supplied splits;small holdouts lack some classes.

The separate296-text benchmark assigns the existing Arabic body-template families per class to train/validation/test BEFORE generating8variants per family. Openings/closings,spelling variation and mixed topics make phrasing imperfect;secondary topics use families from the same split. Seed2026. All five classes occur in each split. Do not combine this benchmark with the feed corpus because their original template families overlap. Neither establishes real-world complaint accuracy.

## Inspection contexts and synthetic visits

The180JSONcontexts use statements,source links,operations,observations and generated visits available by their cutoff. Static register limitations are explicit. Hidden targets/causes are not context inputs. URLs containing forbidden project/developer names are withheld and marked;raw quotes/name mapping are not distributed. Missing images are marked,not invented.

The58visit records are GENERATEDexercises for selected cycles. Dates are working days5–14days after quarter end. Result is progressing/stalled/complete/not_done,using generated cutoff state carried forward plus a fixed8%non-completion draw. Full handover givescomplete;recent progress under1point givesstalled;otherwiseprogressing. Inspector codes are fictional. These are not actual inspections,independent validation or model features. The real-visit template stays empty.

## Validation scope

Base inputs are preserved. Component checks cover split/group separation,masking,scope,unique keys,capacity and generated origins. Tests check future-statement/report exclusion,template separation,quarterly flow semantics and priority behavior. The ZIP has its own SHA-256manifest and executable verifier. Original48-row N=8binary evaluation is historical and does not evaluate the expanded data,current capacity4or new component rules. Censored targets stay null;completion prediction is removed under BINARY_SCOPE_DECISION.md; current targets are binary distressed/not_distressed.
