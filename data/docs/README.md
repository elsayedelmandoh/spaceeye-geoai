# NAC_2026 Synthetic Smart City Dataset — ACUD Graduation Project

Synthetic data only — for Wedjat training only. Not ACUD real data. Not for operational decision-making. Not real NAC statistics.

## District
New Administrative Capital (NAC), Egypt — fictional smart-city training dataset for Wedjat graduation project.

## Zones (6 NAC zones — replaces old Oasis Z01-Z06)
- GOV: Government District (الحي الحكومي) — government
- CBD: Central Business District (حي المال والأعمال) — business
- R3: Residential District 3 / Al-Maqsad (الحي السكني الثالث) — residential
- R7: Residential District 7 (الحي السكني السابع) — residential
- R8: Residential District 8 (الحي السكني الثامن) — mixed/residential
- GRN: Green River (النهر الأخضر) — park/green

Total fictional population ~60,000 (training number only).

## Editions
- Full: 12 months (1 Jan 2026 - 31 Dec 2026), Parquet, ~400-500 MB
- Lite: 4 months (1 Mar 2026 - 30 Jun 2026), CSV, ~100-120 MB
- Lite = exact Mar-Jun slice of full (same seed 2026, same defects/stories within window)

## Time
Africa/Cairo local time, timezone-naive CSV format (compatible with existing course code). LEGACY_CC service_requests store timestamps as UTC (DQ8: mixed formats: YYYY-MM-DDTHH:MM:SSZ and DD/MM/YYYY HH:MM).

Weekend: Friday + Saturday.

## Calendar (2026)
- Ramadan: ~18 Feb - 19 Mar 2026 (approximate Islamic dates — approximate only)
- Eid al-Fitr: ~20-22 Mar 2026
- Eid al-Adha: ~26-29 May 2026
- DST spring: last Friday of Apr 2026 (Apr 24) — clocks jump 00:00 -> 01:00; 23-hour day (gap at 00:xx local)
- DST autumn: last Thursday of Oct 2026 (Oct 29) — clocks fall back; 25-hour day (repeated hour)
- National holidays: Coptic Christmas (Jan 6/7), Revolution Day (Jan 25, Jun 30), Sinai Liberation (Apr 25), Labour Day (May 1), Armed Forces Day (Oct 6)
- Khamsin dust season (spring): Mar-May; 5 dust events (Mar 20; Apr 9-10; May 4-5)

Note: Monorail/LRT/district-cooling numbers and population values are fictional training numbers only. Not ACUD real statistics. Islamic dates are approximate.

## 19 Operational Tables
traffic_counts, network_pressure, bin_fill, electricity_meters, water_meters, bms_readings, parking_occupancy, noise, air_quality, incidents, service_requests, gov_services, collection_trips, work_orders, ops_tickets, camera_status, streetlights, transit_ridership, water_quality

## Planted Defects (DQ1-DQ12)
Recorded in ground_truth/planted_defects.json. Includes: scattered missing, outage blocks, duplicates, DST phantom/gap, impossible values, stuck sensors, Wh unit mismatch (DQ7), mixed timestamp formats (DQ8), category variants (DQ9), orphan sensor TRF-041 (DQ10), late-arriving records (DQ11), slow drift TRF-017 (DQ12).

## Planted Stories (S1-S10) + Day-9 Scenarios (A-E)
Recorded in ground_truth/planted_events.json. Each scenario has verdict DATA or CITY and the evidence clue.

## Complaints (Egyptian Arabic — synthetic)
- complaints_30.csv + complaints_30_key.csv (30 stratified by 6 categories; 8 planted phones; keyword baseline accuracy 100% on this small sample, target was 70-75%)
- complaints_eval_500.csv + complaints_500_key.csv (500 stratified)
- Keyword baseline: data/ground_truth/keyword_baseline.py

## Synthetic Label
Every dataset file, reference table, dictionary, and README includes: "Synthetic data — Wedjat training only. Not ACUD real data. Not for operational decision-making. Not real NAC statistics."
