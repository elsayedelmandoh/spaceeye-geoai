# R1/R2 closure and repository integration

The user authorized a new branch, current-data closure, fetching teammates' work, push and merge. Current scope remains data only. Earlier local no-push notes are superseded by this explicit request.

## Acceptance checklist

- [x] Preserve local R7 work in a checkpoint commit on `feat/r1-r2-data-finalization`.
- [x] Fetch and inspect `origin/main`; initial remote head `ebbab27` had rewritten history relative to local `3487e3f`.
- [x] Integrate the team's complete product docs and dependency/project metadata without replacing them with shortened local documents.
- [x] Retain R7 filtering, small-scope generator handling, scope-scaled checks and the validated `round5_share=0.16`; these were absent from the rewritten remote history.
- [x] Keep historical plans accessible and put current data status/contracts under `docs/data`.
- [x] Add reproducible generators for current R1/R2 reports and actual-schema table dictionaries.
- [x] Verify two identical final data-only builds and preservation of protected artifacts:129artifacts,21table dictionaries;see REPRODUCIBILITY.json.
- [x] Run47tests and independent review of merge/data boundaries;source review found no blocking issue. Final lint/whitespace checks precede commit.
- [ ] Commit clearly under the configured maintainer identity, push branch, integrate latest remote main and merge without force.
- [ ] Verify final remote commit and update the local handoff.

## Integration decisions

The remote's product documents, team roles, structure, references, timeline and `CLAUDE.md` are preserved. The imported product design still contains intended future work; implementation status is linked explicitly to the data contracts. Historical `docs/plan` documents are retained with archive notices rather than discarded.

The incoming metadata renames the package to `spaceeye-geoai`, adds matplotlib and makes dev tools a dependency group. Those changes are accepted and `uv.lock` is regenerated to match them. No unrelated dependency-policy rewrite is introduced.

Raw sources, private names/labels, models and datasets remain outside Git. Public reports contain schemas, aggregate counts and evidence, never private rows. Historical N=8 evaluation is marked as such and no fitting is performed by the delivery check.

## Review notes

During dictionary review, `units_sold` was confirmed to be a monthly flow in the generator. Quarterly totals now sum it instead of taking the last month. A regression test also checks stock behavior and exclusion of a report published after cutoff. Complaint normalization is documented precisely as a cutoff-month sales-flow diagnostic; it is not presented as cumulative buyer incidence.

Evidence is generated in `REPRODUCIBILITY.json`; full local hashes and data-only audits remain under the external app-data directory. A passing data audit is not a claim of current classifier accuracy or actual contractual fine eligibility.
