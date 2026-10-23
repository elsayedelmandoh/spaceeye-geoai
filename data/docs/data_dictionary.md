# Oasis District data dictionary · قاموس بيانات حي الواحة

> **Synthetic data — for training only**
>
> **بيانات اصطناعية لأغراض التدريب فقط**

Fictional district. Not real operational data. Local time Africa/Cairo (with daylight saving), weekend Friday–Saturday.
**Lite** edition: 1 March – 30 June 2025, CSV, 80 metered buildings. **Full** edition: 1 January – 31 December 2025, Parquet, all 327 buildings metered.

<p dir="rtl" align="right">حي افتراضي، وليست بيانات ACUD. التوقيت المحلي للقاهرة، والعطلة الأسبوعية الجمعة والسبت. النسخة المختصرة: من ١ مارس إلى ٣٠ يونيو ٢٠٢٥ بصيغة CSV. النسخة الكاملة: عام ٢٠٢٥ بصيغة Parquet.</p>

**Valid range** is the limit a value must respect to be possible — the rule you clean against and write checks from. Operating targets and alert thresholds are in `docs/kpi_reference.md`.

## Files · الملفات

| Dataset | Pillar | Grain | Rows (lite) | MB (lite) | Rows (full) | MB (full) |
|---|---|---|---:|---:|---:|---:|
| `zones` | Reference | one row per zone | 6 | 0.0 | — | — |
| `roads` | Reference | one row per road segment | — | — | — | — |
| `sensors` | Reference | one row per device | 985 | 0.08 | — | — |
| `assets` | Reference | one row per asset | 755 | 0.05 | — | — |
| `buildings` | Reference | one row per building | 327 | 0.02 | — | — |
| `calendar` | Reference | one row per day of 2025 | 365 | 0.02 | — | — |
| `traffic_counts` | Mobility & Traffic | 15 minutes × traffic counter | 481,560 | 18.4 | 1,442,790 | 5.83 |
| `parking_occupancy` | Mobility & Traffic | hourly × parking lot | 35,124 | 1.11 | 105,120 | 0.2 |
| `transit_ridership` | Mobility & Traffic | daily × line × stop | 2,684 | 0.09 | 8,030 | 0.04 |
| `electricity_meters` | Energy | hourly × building (lite: 80 · full: all 327) | 234,160 | 6.99 | 2,864,520 | 6.15 |
| `streetlights` | Energy | daily × streetlight | 48,800 | 1.35 | 146,000 | 0.18 |
| `water_meters` | Water | hourly × building (lite: 80 · full: all 327) | 234,160 | 6.97 | 2,864,520 | 5.2 |
| `network_pressure` | Water | 15 minutes × measuring point | 233,788 | 7.91 | 700,348 | 1.77 |
| `water_quality` | Water | daily × station | 732 | 0.02 | 2,190 | 0.01 |
| `bin_fill` | Waste | hourly × smart bin | 441,396 | 15.4 | 1,320,570 | 3.22 |
| `collection_trips` | Waste | one row per truck trip | 610 | 0.04 | 1,894 | 0.03 |
| `incidents` | Public Safety & Surveillance | one row per incident | 7,734 | 0.65 | 23,960 | 0.52 |
| `camera_status` | Public Safety & Surveillance | daily × camera | 7,320 | 0.18 | 21,900 | 0.02 |
| `bms_readings` | Buildings & Facilities | hourly × public building (25) | 73,175 | 2.99 | 219,000 | 0.9 |
| `work_orders` | Buildings & Facilities | one row per work order | 436 | 0.03 | 1,238 | 0.03 |
| `air_quality` | Environment | hourly × station (8) | 23,416 | 1.24 | 70,080 | 0.58 |
| `noise` | Environment | hourly × noise point (10) | 29,270 | 0.85 | 87,600 | 0.17 |
| `service_requests` | Government & Citizen Services | one row per request | 10,478 | 2.09 | 44,817 | 0.87 |
| `gov_services` | Government & Citizen Services | daily × service × channel | 1,464 | 0.07 | 4,380 | 0.01 |
| `ops_tickets` | Operations | one row per ticket | 2,063 | 0.21 | 7,118 | 0.14 |

Reference files are shared by both editions. GeoJSON: `reference/zones.geojson` (zone polygons), `reference/roads.geojson` (road segments). Coordinates are fictional (WGS 84, EPSG:4326).

## `zones`

**Reference** · one row per zone. The six zones of Oasis District. Same attributes as zones.geojson, without geometry.

<p dir="rtl" align="right"><b>بيانات مرجعية</b> · صف لكل منطقة. المناطق الست في حي الواحة. نفس خصائص ملف zones.geojson دون الحدود الجغرافية.</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `zone_id` | text |  |  | Z01 | Zone code Z01–Z06 | رمز المنطقة من Z01 إلى Z06 |
| `name_en` | text |  |  | Residential North | Zone name in English | اسم المنطقة بالإنجليزية |
| `name_ar` | text |  |  | سكني شمال | Zone name in Arabic | اسم المنطقة بالعربية |
| `zone_type` | text |  |  | residential | residential · government · business · mixed_use · green_park | نوع المنطقة: سكنية، حكومية، أعمال، متعددة الاستخدامات، متنزه |
| `area_km2` | number | km² | > 0 | 2.07 | Zone area | مساحة المنطقة |
| `population_start` | integer | persons | ≥ 0 | 18000 | Residents on 2025-01-01 | عدد السكان في ١ يناير ٢٠٢٥ |

## `roads`

**Reference** · one row per road segment. Road segments (roads.geojson). Names are invented.

<p dir="rtl" align="right"><b>بيانات مرجعية</b> · صف لكل مقطع طريق. مقاطع الطرق (roads.geojson). الأسماء افتراضية.</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `segment_id` | text |  |  |  | Road segment code RD-01… | رمز مقطع الطريق |
| `name_en` | text |  |  |  | Street name in English | اسم الشارع بالإنجليزية |
| `name_ar` | text |  |  |  | Street name in Arabic | اسم الشارع بالعربية |
| `zone_id` | text |  |  |  | Zone the segment mainly serves | المنطقة التي يخدمها المقطع أساسًا |
| `lanes` | integer | lanes | 1–4 |  | Lanes per direction | عدد الحارات في كل اتجاه |
| `speed_limit_kmh` | integer | km/h | 20–120 |  | Posted speed limit | الحد الأقصى للسرعة |

## `sensors`

**Reference** · one row per device. Sensor registry (the 'sensor' master table). Every device that sends data should be here.

<p dir="rtl" align="right"><b>بيانات مرجعية</b> · صف لكل جهاز. سجل الحساسات (الجدول الرئيسي). يجب أن يظهر هنا كل جهاز يرسل بيانات.</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `sensor_id` | text |  |  | TRF-001 | Device code (TRF, PRS, LOT, WQ, FIL, CAM, AQ, NSE, BMS, EM, WM) | رمز الجهاز |
| `sensor_type` | text |  |  | traffic_counter | Kind of device | نوع الجهاز |
| `pillar` | text |  |  | mobility | Operational pillar | الركيزة التشغيلية |
| `zone_id` | text |  | Z01–Z06 | Z01 | Zone | المنطقة |
| `asset_id` | text |  |  | DET-001 | Physical asset it is mounted on (assets.csv); empty for building meters | الأصل المادي المركّب عليه (assets.csv)؛ فارغ لعدادات المباني |
| `lat` | number | degrees | lat 29.95–29.98 · lon 32.05–32.12 (district box) | 29.971416 | Latitude (fictional) | خط العرض (افتراضي) |
| `lon` | number | degrees | lat 29.95–29.98 · lon 32.05–32.12 (district box) | 32.074025 | Longitude (fictional) | خط الطول (افتراضي) |
| `unit` | text |  |  | vehicles/15min | Measurement unit(s) | وحدة القياس |
| `install_date` | date |  |  | 2023-08-22 | Installation date | تاريخ التركيب |
| `status` | text |  | active · maintenance | active | active · maintenance (registry status, not live health) | الحالة في السجل: يعمل · صيانة |
| `segment_id` | text |  |  | RD-04 | Road segment (traffic counters only) | مقطع الطريق (لعدادات المرور فقط) |

## `assets`

**Reference** · one row per asset. Physical assets that can fail and receive work orders.

<p dir="rtl" align="right"><b>بيانات مرجعية</b> · صف لكل أصل. الأصول المادية التي قد تتعطل وتصدر لها أوامر عمل.</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `asset_id` | text |  |  | DET-001 | Asset code (SL, CAM, BIN, VLV, PMP, DET, TSG, HVAC, …) | رمز الأصل |
| `asset_type` | text |  |  | traffic_detector | Kind of asset | نوع الأصل |
| `pillar` | text |  |  | mobility | Operational pillar | الركيزة التشغيلية |
| `zone_id` | text |  | Z01–Z06 | Z01 | Zone | المنطقة |
| `lat` | number | degrees | lat 29.95–29.98 · lon 32.05–32.12 (district box) | 29.971416 | Latitude (fictional) | خط العرض (افتراضي) |
| `lon` | number | degrees | lat 29.95–29.98 · lon 32.05–32.12 (district box) | 32.074025 | Longitude (fictional) | خط الطول (افتراضي) |
| `install_date` | date |  |  | 2023-08-22 | Installation date | تاريخ التركيب |
| `criticality` | text |  | high · medium · low | medium | high · medium · low | درجة الأهمية: عالية · متوسطة · منخفضة |

## `buildings`

**Reference** · one row per building. All buildings. The lite meter files cover a subset of 80 buildings; the full edition meters all of them.

<p dir="rtl" align="right"><b>بيانات مرجعية</b> · صف لكل مبنى. جميع المباني. ملفات العدادات في النسخة المختصرة تغطي ٨٠ مبنى فقط، وفي النسخة الكاملة كل المباني.</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `building_id` | text |  |  | B-0001 | Building code B-0001… | رمز المبنى |
| `zone_id` | text |  | Z01–Z06 | Z01 | Zone | المنطقة |
| `use_type` | text |  |  | residential | residential · government · commercial · school · mosque · clinic | الاستخدام: سكني، حكومي، تجاري، مدرسة، مسجد، عيادة |
| `floors` | integer | floors | 1–40 | 6 | Number of floors | عدد الطوابق |
| `units` | integer | units | ≥ 1 | 36 | Flats (residential) or tenancies/rooms | عدد الوحدات |
| `lat` | number | degrees | lat 29.95–29.98 · lon 32.05–32.12 (district box) | 29.964508 | Latitude (fictional) | خط العرض (افتراضي) |
| `lon` | number | degrees | lat 29.95–29.98 · lon 32.05–32.12 (district box) | 32.054924 | Longitude (fictional) | خط الطول (افتراضي) |

## `calendar`

**Reference** · one row per day of 2025. Calendar with weekend (Friday, Saturday), holidays, Ramadan, school days and season. Islamic dates come from the Hijri calendar; observed dates may differ by a day.

<p dir="rtl" align="right"><b>بيانات مرجعية</b> · صف لكل يوم في ٢٠٢٥. التقويم: العطلة الأسبوعية (الجمعة والسبت) والإجازات ورمضان والأيام الدراسية والفصل. التواريخ الهجرية محسوبة وقد تختلف بيوم عن الرسمي.</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `date` | date |  |  | 2025-01-07 | Day | اليوم |
| `weekday_en` | text |  |  | Tuesday | Weekday in English | اسم اليوم بالإنجليزية |
| `weekday_ar` | text |  |  | الثلاثاء | Weekday in Arabic | اسم اليوم بالعربية |
| `is_weekend` | 0/1 |  | 0 or 1 | 0 | 1 on Friday and Saturday | ١ يوم الجمعة والسبت |
| `is_holiday` | 0/1 |  | 0 or 1 | 1 | 1 on a public holiday | ١ في الإجازات الرسمية |
| `holiday_en` | text |  |  | Coptic Christmas | Holiday name in English | اسم الإجازة بالإنجليزية |
| `holiday_ar` | text |  |  | عيد الميلاد المجيد | Holiday name in Arabic | اسم الإجازة بالعربية |
| `is_ramadan` | 0/1 |  | 0 or 1 | 0 | 1 during Ramadan | ١ خلال شهر رمضان |
| `is_school_day` | 0/1 |  | 0 or 1 | 0 | 1 on a school day | ١ في أيام الدراسة |
| `season` | text |  |  | winter | winter · spring · summer · autumn | الفصل |

## `traffic_counts`

**Mobility & Traffic** · 15 minutes × traffic counter. Vehicle counts, average speed and lane occupancy from road counters.

<p dir="rtl" align="right"><b>التنقل والمرور</b> · كل ١٥ دقيقة × عداد مرور. أعداد المركبات ومتوسط السرعة ونسبة إشغال الحارة من عدادات الطرق.</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `sensor_id` | text |  | must exist in sensors.csv | TRF-001 | Traffic counter (sensors.csv) | عداد المرور (sensors.csv) |
| `timestamp` | datetime |  | unique per sensor_id (except the repeated DST hour); a real Cairo local time | 2025-03-01 00:00 | Start of the 15-minute interval. Local time, Africa/Cairo (YYYY-MM-DD HH:MM). Daylight saving: clocks forward at 00:00 on 25 Apr 2025, back at the end of 30 Oct 2025. | بداية فترة الـ١٥ دقيقة. التوقيت المحلي للقاهرة (YYYY-MM-DD HH:MM). التوقيت الصيفي: تقديم الساعة في ٢٥ أبريل ٢٠٢٥، وتأخيرها في نهاية ٣٠ أكتوبر ٢٠٢٥. |
| `vehicle_count` | integer | vehicles | 0–1,600 per 15 min | 136.0 | Vehicles counted in the interval (all lanes) | عدد المركبات في الفترة |
| `avg_speed_kmh` | number | km/h | 0–120 | 79.8 | Average speed | متوسط السرعة |
| `occupancy_pct` | number | % | 0–100 | 9.5 | Share of time the detector was occupied | نسبة زمن إشغال الحساس |

## `parking_occupancy`

**Mobility & Traffic** · hourly × parking lot. Occupied spaces per lot.

<p dir="rtl" align="right"><b>التنقل والمرور</b> · كل ساعة × موقف. عدد الأماكن المشغولة في كل موقف.</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `lot_id` | text |  |  | LOT-01 | Parking lot (LOT-01…) | الموقف |
| `timestamp` | datetime |  |  | 2025-03-01 00:00 | Reading time. Local time, Africa/Cairo (YYYY-MM-DD HH:MM). Daylight saving: clocks forward at 00:00 on 25 Apr 2025, back at the end of 30 Oct 2025. | وقت القراءة. التوقيت المحلي للقاهرة (YYYY-MM-DD HH:MM). التوقيت الصيفي: تقديم الساعة في ٢٥ أبريل ٢٠٢٥، وتأخيرها في نهاية ٣٠ أكتوبر ٢٠٢٥. |
| `capacity` | integer | spaces | 1–1,000 | 600 | Total spaces | السعة الكلية |
| `occupied` | integer | spaces | 0 – capacity | 566.0 | Occupied spaces | الأماكن المشغولة |

## `transit_ridership`

**Mobility & Traffic** · daily × line × stop. Bus boardings and alightings per stop, and on-time performance.

<p dir="rtl" align="right"><b>التنقل والمرور</b> · يوميًا × خط × محطة. عدد الركاب الصاعدين والنازلين في كل محطة، ونسبة الالتزام بالمواعيد.</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `date` | date |  |  | 2025-03-01 | Day | اليوم |
| `line_id` | text |  |  | Line A | Line A, Line B or Line C | الخط |
| `stop_id` | text |  |  | A01 | Stop code (A01…) | رمز المحطة |
| `boardings` | integer | passengers | ≥ 0 | 98 | Passengers boarding | الركاب الصاعدون |
| `alightings` | integer | passengers | ≥ 0 | 98 | Passengers alighting | الركاب النازلون |
| `on_time_pct` | number | % | 0–100 | 94.5 | Departures on time at this stop | نسبة الرحلات في موعدها |

## `electricity_meters`

**Energy** · hourly × building (lite: 80 · full: all 327). Electricity consumed in the hour.

<p dir="rtl" align="right"><b>الطاقة</b> · كل ساعة × مبنى (٨٠ في المختصرة · ٣٢٧ في الكاملة). الكهرباء المستهلكة خلال الساعة.</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `building_id` | text |  | must exist in buildings.csv | B-0001 | Building (buildings.csv) | المبنى |
| `timestamp` | datetime |  | unique per building_id (except the repeated DST hour); a real Cairo local time | 2025-03-01 00:00 | Start of the hour. Local time, Africa/Cairo (YYYY-MM-DD HH:MM). Daylight saving: clocks forward at 00:00 on 25 Apr 2025, back at the end of 30 Oct 2025. | بداية الساعة. التوقيت المحلي للقاهرة (YYYY-MM-DD HH:MM). التوقيت الصيفي: تقديم الساعة في ٢٥ أبريل ٢٠٢٥، وتأخيرها في نهاية ٣٠ أكتوبر ٢٠٢٥. |
| `kwh` | number | kWh | 0–600 kWh per building-hour | 38.94 | Energy used in the hour | الطاقة المستهلكة في الساعة |

## `streetlights`

**Energy** · daily × streetlight. Daily status and burning hours of each streetlight.

<p dir="rtl" align="right"><b>الطاقة</b> · يوميًا × عمود إنارة. حالة كل عمود إنارة يوميًا وعدد ساعات تشغيله.</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `asset_id` | text |  |  | SL-0001 | Streetlight (SL-0001…) | عمود الإنارة |
| `date` | date |  |  | 2025-03-01 | Day | اليوم |
| `status` | text |  | on · off · fault | on | on · off · fault | الحالة: يعمل · مطفأ · عطل |
| `burn_hours` | number | hours | 0–14 | 12.74 | Hours lit during the night | ساعات الإضاءة خلال الليل |

## `water_meters`

**Water** · hourly × building (lite: 80 · full: all 327). Water consumed in the hour.

<p dir="rtl" align="right"><b>المياه</b> · كل ساعة × مبنى (٨٠ في المختصرة · ٣٢٧ في الكاملة). المياه المستهلكة خلال الساعة.</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `building_id` | text |  | must exist in buildings.csv | B-0001 | Building (buildings.csv) | المبنى |
| `timestamp` | datetime |  |  | 2025-03-01 00:00 | Start of the hour. Local time, Africa/Cairo (YYYY-MM-DD HH:MM). Daylight saving: clocks forward at 00:00 on 25 Apr 2025, back at the end of 30 Oct 2025. | بداية الساعة. التوقيت المحلي للقاهرة (YYYY-MM-DD HH:MM). التوقيت الصيفي: تقديم الساعة في ٢٥ أبريل ٢٠٢٥، وتأخيرها في نهاية ٣٠ أكتوبر ٢٠٢٥. |
| `m3` | number | m³ | 0–10 m³ per building-hour | 1.125 | Water used in the hour | المياه المستهلكة في الساعة |

## `network_pressure`

**Water** · 15 minutes × measuring point. Pressure and flow in the water network.

<p dir="rtl" align="right"><b>المياه</b> · كل ١٥ دقيقة × نقطة قياس. الضغط والتدفق في شبكة المياه.</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `sensor_id` | text |  | must exist in sensors.csv | PRS-01 | Pressure/flow point (PRS-01…) | نقطة قياس الضغط والتدفق |
| `timestamp` | datetime |  |  | 2025-03-01 00:00 | Reading time. Local time, Africa/Cairo (YYYY-MM-DD HH:MM). Daylight saving: clocks forward at 00:00 on 25 Apr 2025, back at the end of 30 Oct 2025. | وقت القراءة. التوقيت المحلي للقاهرة (YYYY-MM-DD HH:MM). التوقيت الصيفي: تقديم الساعة في ٢٥ أبريل ٢٠٢٥، وتأخيرها في نهاية ٣٠ أكتوبر ٢٠٢٥. |
| `pressure_bar` | number | bar | 0–10 (sensor range) | 4.32 | Network pressure | ضغط الشبكة |
| `flow_lps` | number | L/s | ≥ 0 | 23.2 | Flow through the point | معدل التدفق |

## `water_quality`

**Water** · daily × station. Daily water-quality sample per station.

<p dir="rtl" align="right"><b>المياه</b> · يوميًا × محطة. عينة جودة مياه يومية لكل محطة.</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `station_id` | text |  |  | WQ-01 | Station (WQ-01…) | المحطة |
| `date` | date |  |  | 2025-03-01 | Day | اليوم |
| `chlorine_mg_l` | number | mg/L | 0–5 | 0.66 | Residual chlorine | الكلور المتبقي |
| `turbidity_ntu` | number | NTU | ≥ 0 | 0.29 | Turbidity (cloudiness) | العكارة |
| `ph` | number | pH | 0–14 | 7.46 | Acidity | درجة الحموضة |

## `bin_fill`

**Waste** · hourly × smart bin. Fill level and internal temperature of each bin. 100 means full or overflowing.

<p dir="rtl" align="right"><b>إدارة المخلفات</b> · كل ساعة × حاوية ذكية. نسبة امتلاء كل حاوية ودرجة الحرارة داخلها. القيمة ١٠٠ تعني ممتلئة أو فائضة.</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `bin_id` | text |  | must exist in assets.csv | BIN-001 | Bin (assets.csv, BIN-001…) | الحاوية |
| `timestamp` | datetime |  | unique per bin_id; a real Cairo local time | 2025-03-01 00:00 | Reading time. Local time, Africa/Cairo (YYYY-MM-DD HH:MM). Daylight saving: clocks forward at 00:00 on 25 Apr 2025, back at the end of 30 Oct 2025. | وقت القراءة. التوقيت المحلي للقاهرة (YYYY-MM-DD HH:MM). التوقيت الصيفي: تقديم الساعة في ٢٥ أبريل ٢٠٢٥، وتأخيرها في نهاية ٣٠ أكتوبر ٢٠٢٥. |
| `fill_pct` | number | % | 0–100 | 17.2 | Fill level | نسبة الامتلاء |
| `temp_c` | number | °C | −10–70 | 13.1 | Temperature inside the bin | الحرارة داخل الحاوية |

## `collection_trips`

**Waste** · one row per truck trip. Waste-collection trips.

<p dir="rtl" align="right"><b>إدارة المخلفات</b> · صف لكل رحلة شاحنة. رحلات جمع المخلفات.</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `trip_id` | text |  |  | TRP-00001 | Trip code | رمز الرحلة |
| `truck_id` | text |  |  | TRK-01 | Truck | الشاحنة |
| `route_id` | text |  |  | R01 | Route (R01–R09) | المسار |
| `start_time` | datetime |  |  | 2025-03-01 06:16 | Trip start. Local time, Africa/Cairo (YYYY-MM-DD HH:MM). Daylight saving: clocks forward at 00:00 on 25 Apr 2025, back at the end of 30 Oct 2025. | بداية الرحلة. التوقيت المحلي للقاهرة (YYYY-MM-DD HH:MM). التوقيت الصيفي: تقديم الساعة في ٢٥ أبريل ٢٠٢٥، وتأخيرها في نهاية ٣٠ أكتوبر ٢٠٢٥. |
| `end_time` | datetime |  | after start_time | 2025-03-01 07:46 | Trip end | نهاية الرحلة |
| `bins_collected` | integer | bins | ≥ 1 | 18 | Bins emptied | عدد الحاويات التي أُفرغت |
| `tonnes` | number | t | 0–12 | 0.58 | Waste collected | كمية المخلفات المجمّعة |

## `incidents`

**Public Safety & Surveillance** · one row per incident. Operational incidents (حادث / واقعة تشغيلية). The file is in arrival order (ingested_at).

<p dir="rtl" align="right"><b>السلامة العامة والمراقبة</b> · صف لكل حادث. الحوادث والوقائع التشغيلية. الملف مرتب حسب وقت الوصول (ingested_at).</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `incident_id` | text |  |  | INC-000001 | Incident code | رمز الحادث |
| `timestamp` | datetime |  |  | 2025-03-01 03:11 | When it happened. Local time, Africa/Cairo (YYYY-MM-DD HH:MM). Daylight saving: clocks forward at 00:00 on 25 Apr 2025, back at the end of 30 Oct 2025. | وقت وقوع الحادث. التوقيت المحلي للقاهرة (YYYY-MM-DD HH:MM). التوقيت الصيفي: تقديم الساعة في ٢٥ أبريل ٢٠٢٥، وتأخيرها في نهاية ٣٠ أكتوبر ٢٠٢٥. |
| `zone_id` | text |  |  | Z05 | Zone | المنطقة |
| `type` | text |  |  | illegal_parking | traffic_accident, illegal_parking, vandalism, suspicious_activity, fire_alarm, medical_emergency, road_hazard, crowd_gathering, utility_failure | نوع الحادث |
| `severity` | integer | 1–4 | 1–4 | 4 | 1 critical … 4 low | الخطورة: ١ حرجة … ٤ منخفضة |
| `source` | text |  |  | patrol | CCTV · call · patrol · sensor | مصدر الرصد: كاميرا · اتصال · دورية · حساس |
| `response_min` | number | minutes | ≥ 0 | 28.6 | Minutes from report to first responder on site | الدقائق من البلاغ حتى وصول أول مستجيب |
| `status` | text |  |  | closed | open · in_progress · closed | الحالة |
| `ingested_at` | datetime |  | ≥ timestamp | 2025-03-01 03:20 | When the record reached the data platform | وقت وصول السجل إلى منصة البيانات |

## `camera_status`

**Public Safety & Surveillance** · daily × camera. Daily availability of each CCTV camera.

<p dir="rtl" align="right"><b>السلامة العامة والمراقبة</b> · يوميًا × كاميرا. نسبة إتاحة كل كاميرا يوميًا.</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `camera_id` | text |  |  | CAM-001 | Camera (CAM-001…) | الكاميرا |
| `date` | date |  |  | 2025-03-01 | Day | اليوم |
| `uptime_pct` | number | % | 0–100 | 98.2 | Share of the day the camera was working | نسبة الوقت الذي عملت فيه الكاميرا |

## `bms_readings`

**Buildings & Facilities** · hourly × public building (25). Building management system (BMS) readings.

<p dir="rtl" align="right"><b>المباني والمرافق</b> · كل ساعة × مبنى عام (٢٥). قراءات نظام إدارة المبنى (BMS).</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `building_id` | text |  |  | B-0091 | Building | المبنى |
| `timestamp` | datetime |  |  | 2025-03-01 00:00 | Reading time. Local time, Africa/Cairo (YYYY-MM-DD HH:MM). Daylight saving: clocks forward at 00:00 on 25 Apr 2025, back at the end of 30 Oct 2025. | وقت القراءة. التوقيت المحلي للقاهرة (YYYY-MM-DD HH:MM). التوقيت الصيفي: تقديم الساعة في ٢٥ أبريل ٢٠٢٥، وتأخيرها في نهاية ٣٠ أكتوبر ٢٠٢٥. |
| `indoor_temp_c` | number | °C | 5–45 °C | 16.9 | Indoor temperature | درجة الحرارة الداخلية |
| `humidity_pct` | number | % | 0–100 | 57.0 | Indoor relative humidity | الرطوبة النسبية الداخلية |
| `hvac_kw` | number | kW | ≥ 0 | 1.2 | Cooling (HVAC) power | قدرة التكييف |
| `occupancy_count` | integer | persons | ≥ 0 | 0.0 | People inside | عدد الأشخاص داخل المبنى |

## `work_orders`

**Buildings & Facilities** · one row per work order. Maintenance work orders on assets.

<p dir="rtl" align="right"><b>المباني والمرافق</b> · صف لكل أمر عمل. أوامر عمل الصيانة على الأصول.</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `work_order_id` | text |  |  | WO-00001 | Work order code | رمز أمر العمل |
| `asset_id` | text |  |  | TSG-08 | Asset (assets.csv) | الأصل |
| `opened_at` | datetime |  |  | 2025-03-01 00:03 | Opened. Local time, Africa/Cairo (YYYY-MM-DD HH:MM). Daylight saving: clocks forward at 00:00 on 25 Apr 2025, back at the end of 30 Oct 2025. | وقت الفتح. التوقيت المحلي للقاهرة (YYYY-MM-DD HH:MM). التوقيت الصيفي: تقديم الساعة في ٢٥ أبريل ٢٠٢٥، وتأخيرها في نهاية ٣٠ أكتوبر ٢٠٢٥. |
| `closed_at` | datetime |  | after opened_at, or empty | 2025-03-05 10:04 | Closed (empty if still open) | وقت الإغلاق (فارغ إن كان مفتوحًا) |
| `category` | text |  |  | Traffic signal | Streetlight, HVAC, CCTV, Water network, Waste bin, Traffic signal, Sensor | فئة العمل |
| `priority` | text |  | P1–P4 | P4 | P1 (urgent) … P4 | الأولوية |
| `sla_hours` | integer | hours | 4 · 24 · 72 · 168 | 168 | Target time to close: P1 4, P2 24, P3 72, P4 168 | الزمن المستهدف للإغلاق |
| `status` | text |  |  | closed | open · in_progress · closed | الحالة |

## `air_quality`

**Environment** · hourly × station (8). Air pollutants and weather at each station.

<p dir="rtl" align="right"><b>البيئة</b> · كل ساعة × محطة (٨). ملوثات الهواء والطقس في كل محطة.</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `station_id` | text |  |  | AQ-01 | Station (AQ-01…) | المحطة |
| `timestamp` | datetime |  |  | 2025-03-01 00:00 | Start of the hour. Local time, Africa/Cairo (YYYY-MM-DD HH:MM). Daylight saving: clocks forward at 00:00 on 25 Apr 2025, back at the end of 30 Oct 2025. | بداية الساعة. التوقيت المحلي للقاهرة (YYYY-MM-DD HH:MM). التوقيت الصيفي: تقديم الساعة في ٢٥ أبريل ٢٠٢٥، وتأخيرها في نهاية ٣٠ أكتوبر ٢٠٢٥. |
| `pm25` | number | µg/m³ | 0–1,000 | 27.9 | Fine particles PM2.5 | الجسيمات الدقيقة PM2.5 |
| `pm10` | number | µg/m³ | 0–2,000 | 63.6 | Particles PM10 (dust) | الجسيمات PM10 (الغبار) |
| `no2` | number | ppb | 0–500 | 20.2 | Nitrogen dioxide | ثاني أكسيد النيتروجين |
| `o3` | number | ppb | 0–300 | 17.1 | Ozone | الأوزون |
| `temp_c` | number | °C | −5–55 | 10.6 | Air temperature | درجة حرارة الهواء |
| `humidity_pct` | number | % | 0–100 | 78.0 | Relative humidity | الرطوبة النسبية |

## `noise`

**Environment** · hourly × noise point (10). Average noise level in the hour.

<p dir="rtl" align="right"><b>البيئة</b> · كل ساعة × نقطة قياس (١٠). متوسط مستوى الضوضاء خلال الساعة.</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `sensor_id` | text |  |  | NSE-01 | Noise point (NSE-01…) | نقطة قياس الضوضاء |
| `timestamp` | datetime |  |  | 2025-03-01 00:00 | Start of the hour. Local time, Africa/Cairo (YYYY-MM-DD HH:MM). Daylight saving: clocks forward at 00:00 on 25 Apr 2025, back at the end of 30 Oct 2025. | بداية الساعة. التوقيت المحلي للقاهرة (YYYY-MM-DD HH:MM). التوقيت الصيفي: تقديم الساعة في ٢٥ أبريل ٢٠٢٥، وتأخيرها في نهاية ٣٠ أكتوبر ٢٠٢٥. |
| `laeq_db` | number | dB(A) | 20–130 | 55.3 | Equivalent continuous sound level | مستوى الصوت المكافئ |

## `service_requests`

**Government & Citizen Services** · one row per request. Citizen requests and complaints. Contains synthetic personal-data fields for the Day 3 masking practice.

<p dir="rtl" align="right"><b>الخدمات الحكومية وخدمات المواطنين</b> · صف لكل طلب. طلبات وشكاوى المواطنين. يحتوي على حقول بيانات شخصية اصطناعية لتمرين الإخفاء في اليوم الثالث.</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `request_id` | text |  |  | SR-000001 | Request code | رمز الطلب |
| `created_at` | datetime |  |  | 2025-03-01 05:00 | Created. CRM rows: local time. LEGACY_CC rows: UTC, mixed formats. | وقت الإنشاء. صفوف CRM بالتوقيت المحلي، وصفوف LEGACY_CC بتوقيت UTC وبصيغ مختلفة. |
| `channel` | text |  | app · call_centre · service_centre | call_centre | app · call_centre · service_centre | القناة: التطبيق · مركز الاتصال · مركز الخدمة |
| `category` | text |  | one of the 15 canonical Arabic labels | مخالفات الانتظار | One of 15 categories (canonical Arabic labels) | فئة من ١٥ فئة (أسماء عربية معتمدة) |
| `zone_id` | text |  | Z01–Z06 | Z03 | Zone | المنطقة |
| `description_ar` | text |  |  | parking مقفول ومفيش أماكن خالص | Free text from the citizen (Egyptian Arabic, some English and Franco-Arabic) | نص حر من المواطن (عامية مصرية مع بعض الإنجليزية والفرانكو) |
| `status` | text |  | open · in_progress · closed | closed | open · in_progress · closed | الحالة |
| `closed_at` | datetime |  |  | 2025-03-07 04:26 | Closed (same time rules as created_at) | وقت الإغلاق (بنفس قواعد created_at) |
| `satisfaction_1_5` | integer | 1–5 | 1–5 or empty | 2.0 | Satisfaction survey (empty if not answered) | رضا المواطن (فارغ إن لم يُجب) |
| `requester_name` | text |  |  | ياسمين نبيل | SYNTHETIC personal data — generic name list | بيانات شخصية اصطناعية — اسم من قائمة عامة |
| `requester_phone` | text |  |  | +20 100 000 0594 | SYNTHETIC personal data — reserved fake pattern +20 100 000 xxxx | بيانات شخصية اصطناعية — رقم وهمي بنمط محجوز |
| `source_system` | text |  |  | CRM | CRM · LEGACY_CC (the two source systems) | النظام المصدر |

## `gov_services`

**Government & Citizen Services** · daily × service × channel. Government service transactions. Service centres are closed on Friday, Saturday and holidays.

<p dir="rtl" align="right"><b>الخدمات الحكومية وخدمات المواطنين</b> · يوميًا × خدمة × قناة. معاملات الخدمات الحكومية. مراكز الخدمة مغلقة الجمعة والسبت والإجازات.</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `date` | date |  |  | 2025-03-01 | Day | اليوم |
| `service_type` | text |  |  | building_permit | building_permit, utility_connection, residency_registration, business_licence, parking_permit, certificate_request | نوع الخدمة |
| `channel` | text |  |  | online | online · service_centre | القناة |
| `transactions` | integer | count | ≥ 0 | 5 | Transactions completed | عدد المعاملات |
| `avg_processing_days` | number | days | ≥ 0, empty when no transactions | 14.0 | Average processing time (empty when no transactions) | متوسط زمن الإنجاز |

## `ops_tickets`

**Operations** · one row per ticket. Operations-centre tickets (تذكرة) and escalations (تصعيد).

<p dir="rtl" align="right"><b>التشغيل</b> · صف لكل تذكرة. تذاكر مركز العمليات وحالات التصعيد.</p>

| Column | Type | Unit | Valid range | Example | Description | الوصف |
|---|---|---|---|---|---|---|
| `ticket_id` | text |  |  | OPS-000001 | Ticket code | رمز التذكرة |
| `created_at` | datetime |  |  | 2025-03-01 08:21 | Opened. Local time, Africa/Cairo (YYYY-MM-DD HH:MM). Daylight saving: clocks forward at 00:00 on 25 Apr 2025, back at the end of 30 Oct 2025. | وقت الفتح. التوقيت المحلي للقاهرة (YYYY-MM-DD HH:MM). التوقيت الصيفي: تقديم الساعة في ٢٥ أبريل ٢٠٢٥، وتأخيرها في نهاية ٣٠ أكتوبر ٢٠٢٥. |
| `pillar` | text |  |  | mobility | Pillar the ticket belongs to | الركيزة |
| `source` | text |  |  | manual | alert · manual · citizen | المصدر: تنبيه · يدوي · مواطن |
| `severity` | integer | 1–4 | 1–4 | 2 | 1 critical … 4 low (training matrix) | الخطورة: ١ حرجة … ٤ منخفضة |
| `status` | text |  |  | resolved | open · in_progress · resolved · closed | الحالة |
| `escalated` | boolean |  |  | False | True if escalated | هل صُعّدت التذكرة |
| `escalated_to_role` | text |  |  |  | shift_supervisor · pillar_owner · field_dispatcher | الدور الذي صُعّدت إليه |
| `resolved_at` | datetime |  | after created_at, or empty | 2025-03-02 03:58 | Resolved (empty if not yet) | وقت الحل |
| `handover_note` | text |  |  | تم إبلاغ المواطنين عبر التطبيق | Note for the next shift (Arabic) | ملاحظة تسليم الوردية |
