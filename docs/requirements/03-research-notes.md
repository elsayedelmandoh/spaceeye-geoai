# Research notes

## Egypt DST and Ramadan/Eid calendar, 2026

*Synthetic data — spaceeye-geoai training only. Feeds `config/extension.yaml` and `extend_2026.py` (plan §4.4, §4.8). Researched 20 Oct 2026.*

## Question
Which exact clock transitions apply in Africa/Cairo in 2026, so the generated 2026 horizon has the right 23h and 25h days?

## Findings
| Item | Value | Source |
|---|---|---|
| Rule | DST runs from the last Friday of April to the last Thursday of October | Egypt Today, 9 Apr 2026 and 26 Aug 2026; Egypt Independent |
| Spring 2026 | Fri 24 Apr 2026, clocks 00:00 → 01:00. Local hour 00:xx does **not exist**; the day has 23 hours | timeanddate.com (Egypt 2026) |
| Autumn 2026 | Clocks go back at 00:00 on Fri 30 Oct, to 23:00 on **Thu 29 Oct 2026**. Hour 23:xx on 29 Oct occurs **twice**; that day has 25 hours | timeanddate.com; 24timezones.com |
| Offsets | UTC+2 standard (EET), UTC+3 in DST (EEST) | 24timezones.com |
| History | DST abolished 2016, reinstated 2023 | Egypt Today; Egypt Independent |

## Ramadan and Eid 2026 (Egypt)
| Item | Date | Status | Source |
|---|---|---|---|
| Ramadan start | Thu 19 Feb 2026 | Announced by Dar al-Ifta (17 Feb) | Cairo Scene; Calendarific |
| Ramadan end | Fri 20 Mar 2026 (30 days: 19 Feb–20 Mar) | Expected | Cairo Scene (30-day month) |
| Eid al-Fitr | Sat 21 Mar 2026, holiday continues Sun 22 Mar | Expected, subject to moon sighting | Cairo Scene; Calendarific |
| Arafat Day | Tue 26 May 2026 | Calendar listing | Calendarific |
| Eid al-Adha | Wed 27 May 2026, holiday continues Thu 28 May | Calendar listing, tentative | Calendarific |
| Islamic New Year | Wed 17 Jun 2026 | Calendar listing | Calendarific |

Some sites give other dates (for example Eid al-Fitr on 20 Mar, or Eid al-Adha on 26 Jun). I discarded them: they are unsourced or inconsistent with the Dar al-Ifta Ramadan start. For comparison, the 2025 kit has 29 Ramadan days (1–29 Mar).

## Consequences for the plan
- The 2025 pattern holds: the spring gap is a Friday (25 Apr 2025, 24 Apr 2026), so Fri–Sat weekend logic and the gap interact only on a Friday.
- `reference/calendar` covers 2025 only, so 2026 transitions must come from the statutory rule above, not from a calendar lookup. Plan §4.4 ("never hard-code, read from calendar") needs a rule-based generator for 2026.
- The autumn repeat is at 23:xx, not 01:xx. De-duplication must be tz-aware (`ambiguous` handling) or real readings are deleted.

## Open conflicts
- Sources disagree on the statute number (Law No. 24 vs No. 34 of 2023). Do not cite a law number in the deck until verified.
- Eid al-Fitr and Eid al-Adha dates below are expected, not announced by Dar al-Ifta in the sources found. Confirm before final claims. Egypt often grants extra days off, so holiday length is tentative.

## Sources
- https://www.timeanddate.com/time/change/egypt?year=2026
- https://24timezones.com/Egypt/time
- https://www.egypttoday.com/Article/1/146268/One-hour-ahead-Daylight-saving-time-to-be-applied-April
- https://www.egypttoday.com/Article/1/149096/When-will-daylight-saving-time-end-in-2026
- https://www.egyptindependent.com/egypt-to-implement-daylight-saving-time-on-friday/
- https://cairoscene.com/Buzz/First-Day-of-Ramadan-Is-Thursday-February-19th
- https://calendarific.com/holidays/2026/EG
