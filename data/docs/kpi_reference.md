# KPI Reference — NAC_2026 Smart City Dataset

Synthetic reference only — Wedjat graduation project. Not ACUD operational metrics.

## Energy (Energy module — electricity_meters)
- Avg kWh/building/day: mean(kwh) per metered building / day.
- Seasonal sinusoid: summer > winter. District-cooling buildings (B-0112 GOV, B-0240 CBD, B-0269 R7) have lower on-site cooling load (utility-side peak shown in BMS/utility meters).
- Off-hours waste (S4): GOV and CBD buildings maintain near-daytime HVAC/lighting on Friday-Saturday nights and evenings — detectable as elevated night kWh.
- DQ7: exactly 3 metered buildings use Wh instead of kWh (values x1000) — must be corrected before aggregation.

## Water (Water module — network_pressure, water_meters, water_quality)
- Night-flow rise (leak): night_flow (02:00-05:00) / mean_flow; slow rise over ~3 weeks = irrigation leak (S3 GRN); fast rise with pressure collapse + flow x2.5 + complaint cluster = main break (S3 R7).
- Water meters: m3/hour; approximate conversion m3 ≈ flow_lps * 0.9 / 1000 (simplified synthetic model).
- Water quality: chlorine (0.2-2.0 mg/L), turbidity (0.1-5.0 NTU), pH (6.0-9.0) per station (STN-01..STN-08, 4-hour intervals).

## Waste (Waste module — bin_fill, collection_trips)
- Overflow rate by zone: overflow_hours / bins per zone; deliberate count-vs-rate trap: R7 (most overflow hours due to highest bin count) vs GRN (highest overflow rate due to fewest bins).
- Trip efficiency: tonnes per trip; route-level fallback when bin_id is empty (~10% of trips have empty bin_id for route-level aggregation).

## Mobility (Mobility module — traffic_counts, parking_occupancy, transit_ridership)
- Traffic counts: 15-min intervals per registered traffic sensor; DQ10 ghost TRF-041 (present in traffic_counts, absent from sensors.csv) creates orphan-key mismatch; DQ12 TRF-017 slow drift (+1%/week); stuck counter TRF-023 frozen 11h (Jun 10) (S9).
- Parking occupancy: 12 lots (PKL-01..PKL-12) with capacity; peak occupancy ~95%, weekends lower; DQ5 impossible values (occupied > capacity) at ~0.1%.
- Transit ridership: Monorail + LRT + 3 bus routes; daily boardings; on-time % ~75-98%; S1 ramp shifts peak patterns.

## Citizen Services (citizen module — service_requests, gov_services, ops_tickets)
- App channel share: app requests / total requests; S7 (app launch week Sep 7-13) creates '+85% complaints' headline that is really a channel-launch effect.
- Service request categories (6 official): Water, Electricity, Streetlights, Waste, Traffic/Roads, Public_Safety. Category spelling variants recoverable via canonical map (DQ9).
- LEGACY_CC (DQ8): ~10% of requests have created_at in mixed UTC formats (YYYY-MM-DDTHH:MM:SSZ or DD/MM/YYYY HH:MM); CRM uses local YYYY-MM-DD HH:MM.
- Phone planting (DQ): 8 planted fictional phones in description_ar (+20 100 000 0000, 010...), clearly synthetic/unassigned patterns; requester_name synthetic Arabic names (no real data).
- Late incidents (DQ11): ~2% of incidents have created_at after event time.
- Keyword baseline: 30-sample accuracy = 100% (exceeds 70-75% target); regex finds 8/8 planted phones.

## Public Safety (public_safety module — incidents, camera_status)
- Incident severity: 1-4 per zone; linked to citizen services via zone and time proximity.
- Camera status: 60 cameras (CAM-001..CAM-060), hourly/daily status; DQ6 frozen/missing periods (TRF-023 frozen; AQ-03 frozen Mar 17-20; AQ-06 frozen May 25-28).

## Environment (environment module — noise, air_quality)
- Noise: dBA per noise sensor; peaks with traffic; spikes during events (S6 Khamsin dust episodes Mar-May raise noise + AC load).
- Air quality: PM10, PM2.5, NO2 per station; Khamsin episodes spike PM10; synthetic with archive seasonal profile.
- DST transition: spring gap (Apr 24: 23-hour day, no 00:00-00:59 local); autumn repeat (Oct 29: 25-hour day, repeated hour). Meters follow DST correctly; gateway/traffic sensors ignore DST (phantom rows, DQ4).
