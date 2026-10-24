# Dataset — spaceeye-geoai Data Architecture, External Benchmarks & Deterministic Synthetic Generator

> **Mandatory Notice:** `Synthetic data — spaceeye-geoai training only. Not for operational decision-making.`[cite: 1, 2, 3]

---

## 1. Where to Get the Datasets (Primary Sources & Links)

The **spaceeye-geoai** project (`ACUD_Oasis` synthetic district, 60,000 residents across 6 zones `Z01–Z06`) relies on two categories of data[cite: 1, 2, 3]:

1. **The Local ACUD Program Kit (`data/lite/`, `data/full/`, `reference/`)**: Provided locally in the course environment, containing 12 planted data-quality defects and 8 operational stories[cite: 1, 5, 6].
2. **External Cyber-Physical Security Benchmark Datasets**: If you want to benchmark or calibrate your anomaly detection models against real-world industrial/smart-city attack traces (as noted in the project research options)[cite: 4], use these verified primary sources:

| Dataset Name                                                  | Primary Owner / Institution                                  | Use Case in spaceeye-geoai                                                                                                                                         | Official Primary URL / Access Link                                                                                                                                                                                                                                                              |
| :------------------------------------------------------------ | :----------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **TON_IoT Telemetry & Network Dataset**                 | UNSW Canberra Cyber (Dr. Nour Moustafa)                      | Smart-city IoT sensor telemetry spoofing, MQTT/Modbus injection, and DDoS/botnet patterns (`L1`/`L2` calibration)[cite: 4].                                    | • Primary Portal: [https://research.unsw.edu.au/projects/toniot-datasets](https://research.unsw.edu.au/projects/toniot-datasets)• Mirror (Kaggle): [https://www.kaggle.com/datasets/arnobbhowmik/ton-iot-network-dataset](https://www.kaggle.com/datasets/arnobbhowmik/ton-iot-network-dataset) |
| **BATADAL (Battle of the Attack Detection Algorithms)** | SUTD iTrust & Politecnico di Milano (Taormina et al.)        | Concealed SCADA cyber-physical attacks on water distribution networks, pump/valve manipulation, and pressure drops (`L5` hydraulic strike calibration)[cite: 4]. | • Primary Archive (CISPA/Figshare DOI): [https://doi.org/10.60882/cispa.32772453](https://doi.org/10.60882/cispa.32772453)• Paper & Specs: [https://www.mdpi.com/2073-4441/13/9/1247](https://www.mdpi.com/2073-4441/13/9/1247)                                                                 |
| **SWaT (Secure Water Treatment Testbed)**               | iTrust, Singapore University of Technology and Design (SUTD) | 11-day physical & network cyber-attack time series across sensors (`FIT`, `LIT`) and motorized valves (`MV`)[cite: 4].                                       | • Primary Portal: [https://www.sutd.edu.sg/itrust/itrust-labs/datasets/dataset-characteristics/swat/](https://www.sutd.edu.sg/itrust/itrust-labs/datasets/dataset-characteristics/swat/)                                                                                                        |

> **Hard Program Rule:** You do **not** need to download gigabytes of external PCAPs to pass the rubric. All teams work in the same `ACUD_Oasis` district and extend the kit with deterministic Python-generated synthetic data (`SEED = 42`), a complete data dictionary per table, `provenance='synthetic'`, and an answer key (`planted_stories.csv`).

---

## 2. Scope & Pillar Filtering (Frozen v3.3 Rules)

Only the **three kept pillars** are included in the spaceeye-geoai build:

1. **Energy / Power & Buildings** (`electricity_meters`, `bms_readings`, `streetlights`, `buildings`)[cite: 1]
2. **Smart Water Network** (`network_pressure`, `water_meters`, `work_orders`)[cite: 1]
3. **Citizen Services & Maintenance Governance** (`service_requests`, `gov_services`, `incidents`, `camera_status`, `traffic_counts`, `assets`, `sensors`)[cite: 1, 5]

*(Note: Waste `bin_fill`/`collection_trips` and Environment `air_quality` are cut from scope and must not be added to the production pipeline, though kit lessons on uniqueness and count-vs-rate remain valid.)*[cite: 1, 2, 6]

---

## 3. Directory Layout & File Inventory

```text
spaceeye-geoai/
├── reference/
│   ├── zones.csv                     # Z01..Z06 metadata & population
│   ├── calendar.csv                  # 2025 dates, is_ramadan, is_weekend, is_holiday, is_dst_transition
│   ├── sensors.csv                   # Registry of TRF, PRS, CAM, ELEC sensors -> zone_id
│   ├── buildings.csv                 # B-0001..B-0300 metadata -> zone_id
│   ├── assets.csv                    # Valves, transformers, pumps, streetlights
│   └── zones.geojson                 # Spatial polygons for Z01..Z06
├── data/
│   ├── lite/                         # CSVs: 2025-03-01 to 2025-06-30 (daily dev & replay)
│   │   ├── electricity_meters.csv    # Hourly building kWh (includes Wh unit defects on B-0112, B-0240, B-0269)
│   │   ├── bms_readings.csv          # Hourly indoor_temp_c, cooling_load_kw, hvac_status (B-0198 in °F)
│   │   ├── network_pressure.csv      # 15-min pressure_bar & flow_m3h per sensor (PRS-01..PRS-18)
│   │   ├── traffic_counts.csv        # 15-min vehicle_count, avg_speed_kmh, occupancy_pct
│   │   ├── streetlights.csv          # Daily/event fault_rate_pct & status per corridor
│   │   ├── camera_status.csv         # Daily/event uptime_pct & status per camera
│   │   ├── service_requests.csv      # Citizen complaints with Arabic text & requester_phone
│   │   ├── work_orders.csv           # Maintenance tickets, SLA hours, status
│   │   ├── incidents.csv             # Field safety/traffic incidents
│   │   └── gov_services.csv          # Digital portal service logs
│   └── synthetic/                    # spaceeye-geoai CRS-05 extensions (all provenance='synthetic')
│       ├── critical_assets.csv       # Sovereign targets (City Bank HQ, City Tower, Data Center)
│       ├── threat_advisory_feed.csv  # Pre-attack T-72h intelligence advisories
│       ├── probe_events.csv          # T-72h 03:00 AM SCADA/BMS reconnaissance pings
│       ├── response_units.csv        # Police, Civil Defense, Rapid Intervention units
│       ├── route_candidates.csv      # Corridor options (Central Axis vs Z06 Green Park safe route)
│       ├── bot_complaints_overlay.csv# L2: ~400 templated Arabic complaints in Z01 (<60s)
│       ├── drill_overlay.parquet     # Combined L1-L5 & Control windows non-destructive overlay
│       └── planted_stories.csv       # Ground-truth Answer Key for evaluation
└── scripts/
    └── generate_synthetic_data.py    # Deterministic generator (SEED = 42)
```
