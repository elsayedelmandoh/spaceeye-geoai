# Data governance cards

Task T-SA-04. Roles below are proposed operational responsibilities. No institutional approval or named-member sign-off is asserted. The source/generation register is [documented here](../../data/DATA_SOURCES_AND_GENERATION.md).

| Data group | Accountable role | Origin | Refresh | Permitted working access | Sharing and limits |
| --- | --- | --- | --- | --- | --- |
| Compound register and boundaries | Track A data owner | Public/derived, with field-specific generated assumptions | Review with each source/boundary update | Team: coded prepared fields; custodian: private mapping | Working polygons are not legal boundaries; no names/mapping in team exports |
| Satellite/annual context and statements | Track A / GIS owner | Public observations, published claims, derived activity and approved height estimates | Quarterly satellite preparation; annual context only when supported; facts on publication | Team: accepted coded outputs; source audit access restricted as appropriate | Preserve capture/publication dates, record IDs, licenses and unknowns; no later-height claims |
| KPI, cycle list and quality logs | Track A rule owner | Derived from cutoff-available public observations | After accepted source/configuration update | Team and authorized committee through reviewed exports | Explain priorities; retain lineage/FLAGs; generated inputs do not enter real Track A |
| Finance, complaints and fine assumptions | Track B generator owner | Synthetic / derived from synthetic | Seeded rebuild after reviewed generator/configuration change | Team: prepared masked tables | Retain synthetic label; not actual finances, contracts, fines or complaints |
| Raw defects, quarantines, truth and identity mapping | Data custodian / generator owner | Private inputs and evaluation-only truth | Preserve per version; review before any new access | Minimum authorized maintainers only | Excluded from ready bundle; no hidden truth as X or as agent context |
| ML exports and complaint corpora | Track B / AI owner | Mixed observed features and generated features/targets, explicitly separated | With accepted dataset version | Team: approved export and declared split | Preserve time/family splits; do not merge complaint corpora; no independent real-world accuracy claim |
| Inspection JSON contexts | AI component owner | Cutoff-controlled public facts plus separated generated context | With accepted preparation/cutoff version | Team; external provider only after appropriate configuration/review | No private mappings or truth; no images bundled; context is not a verified AI inspection file |
| Visits and financial-priority exercises | Operations / Track B owner | Explicitly synthetic or hypothetical | With accepted scenario configuration | Team demonstration/training | Not actual visits, independent validation or operational forecasts |
| Future actual field records | Authorized operations custodian | Not yet collected in this delivery | After each authorized visit | Role-limited access agreed before collection | Use a separate real-record location and retention policy; never mix with synthetic exercises |

## Version and change controls

Use feature branches and reviewed PRs. Keep source identifiers, publication cutoffs, configuration/code revision, per-field origins and manifests. Retain raw evidence outside public Git. Separate private evaluation targets from features. Publish only the approved allowlisted prepared bundle; a code-only documentation change does not change the published dataset version.

STOP blocks delivery; FIX requires correction and rerun; FLAG requires a recorded review decision. The current 2019Q2 flag remains open. Review output masking and coded-only export controls after schema changes. The current roles do not imply that a teammate has accepted a result.

Before collecting real sensitive data, the custodian must agree purpose, authorized recipients, access controls and retention/deletion policy. No universal retention period or existing production security control is invented here. See [responsible use](responsible-ai.md).
