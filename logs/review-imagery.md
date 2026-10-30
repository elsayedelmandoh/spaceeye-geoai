# Imagery code review record - 30 October 2026

Scope: imagery source selection, inspector pairs, capture/publication cutoffs, metadata-only delivery, local installation and HTML rendering. Reviewed implementation revisions include `6d81de3`, `69f449c` and the focused fixes below. Limits: code review did not independently rerun external rendering or validate imagery against field truth. Assigned task-review acceptance remains pending.

| Finding | Resolution | Evidence |
| --- | --- | --- |
| JSON-only restoration could return a capture after a requested partial-period end. | An unconditional capture-window guard runs before persistence/rendering. | `6cc0118`; JSON-only restoration regression. |
| Some scene paths checked bad classes without enforcing the 95% valid-coverage limit. | Candidate, cache and final acceptance check both thresholds and all compound codes. | `6cc0118`; boundary and invalid-coverage regressions. |
| Latest accepted Wayback capture is July 2025 and could be mistaken for current imagery. | Pair/timeline metadata and gallery/inspector captions show completed-month capture age at the as-of. Historical requests recompute age. | `09f6416`; date-age and caption checks; current after images are 14 months old at 2026-09-30. |
| HTML containing base64 Esri pixels could be mistaken for freely publishable output. | Imagery/T-EL-06 guidance explicitly keeps such HTML local; it is never committed or redistributed. | Third-party notice, imagery guide and task-board condition. |

The first two findings received a focused code recheck with no outstanding findings. The subsequent two items implement the recorded conditional review requests. Current validation: **240 tests passed**, touched-source Ruff passed, local report/member hashes validated, metadata name scan passed, and a separate data root/different working directory installed numerical v6 plus the offline report without external source access. This records review evidence and fixes, not a signature or acceptance on behalf of the assigned reviewer.

The numerical v6 ZIP is unchanged by imagery. Esri pixels, generated inspection HTML and report ZIPs stay outside Git. No model fitting, numerical threshold changes, or finishing/road-timing claims were introduced.
