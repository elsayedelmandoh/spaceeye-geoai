# T-AH-14: K1 fallback switch and its effect

Spec section 13: "A fails on new quarters → fall back to K1 (DW change), state the narrower claim."

## Switch
In `configs/data.yaml`, add `source: k1` under `activity:`. The default (key absent or `model`) keeps the activity score A. Implementation: `activity.apply_source` (`src/pipeline/activity.py`), used by every scoring call (full run, backtest variant, frozen-clock check). With `k1`:
- active = K1 > `k1_active` (0.02);
- `activity_prob` stays empty;
- an unknown K1 stays unknown, never "inactive".

Tests: `tests/test_activity_fallback.py`.

When to switch: only if A fails its acceptance tests (T1, T2, T3, seasonal spread) on new quarters, and only by a recorded decision before looking at the levels. Changing the key changes `run_id`. Then run `make run` and `full_repro`. The claim narrows to "Dynamic World built-probability change" (no Sentinel-2 or class-share features, no validated activity probability).

## Effect on the current data
Computed in memory on 30 October 2026, run R1-1846440cf3. Nothing was written to app_data. Same tables, same models.

| | A (current) | K1 fallback |
| --- | --- | --- |
| Active compound-quarters | 0.667 | 0.503 |
| Levels at 2026Q3 (1/2/3/4) | 1 / 2 / 3 / 6 | 3 / 0 / 2 / 7 |
| Compounds whose level changes at 2026Q3 | — | 3 of 12 |
| Cycle list (capacity 4) | C18, C07, C14, C03 | C07, C14, C18, C12 |
| Backtest: after start / point in time / literal (of 6) | 1 / 0 / 2 | 2 / 1 / 4 |

**Reading.**
- K1 flags fewer quarters active, so more compounds reach level 1 through K2.
- The backtest moves from 1 to 2 of 6. That is still far below the fixed criterion of 5 of 6.
- **This is not a reason to switch.** A was chosen over K1 by the pre-registered T1-T3 tests (balanced accuracy +3.0 and +5.1 points, false alarms 9.1 % vs 20.5 %), and picking a variant because its backtest count looks better is result-driven selection.
- The switch exists for the failure case only.
