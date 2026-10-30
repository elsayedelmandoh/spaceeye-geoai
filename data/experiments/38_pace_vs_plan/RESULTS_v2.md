# K7 v2: result 2026-10-30. **Not testable** (PROTOCOL_v2.md, hash 986f4448…, verified)

- **Truth:** `39_delivery_truth/DELIVERY_TRUTH_R2.md` and `delivery_truth.csv`, from audited records plus Arabic and English web search.
- **Independent set** (R8 plus R7 outside the 6 cases):
  - with C18 (n = 16): 0 on_time, 2 delayed (C15, C16), 14 unknown;
  - without C18 (n = 15): 0 on_time, 2 delayed, 13 unknown.
- **Gate:** it needs at least 2 on_time and at least 3 delayed. **Not met, so the result is "not testable", final for this version.** No K7 v2 value was computed, because none would be evaluated.
- **Context:**
  - Of all 22 compounds, every one with a known class is delayed (8 delayed, 0 on time).
  - This is consistent with v1's alerts on all 7 R7 compounds with a plan being correct, but it does not prove it. The indicator cannot be shown to stay quiet on an on-time compound, because no such compound is publicly documented.
- **Decision:** K7 stays a displayed context indicator, with the v1 numbers (`RESULTS.md`).
- **What would make it testable:** ACUD's own contract dates and handover records, which would supply the on-time compounds that public sources lack.
