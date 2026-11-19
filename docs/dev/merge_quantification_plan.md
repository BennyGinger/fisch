# Merge quantification across independent runs

Status: future plan; not implemented. This is separate from opening a fresh run
containing portable acquisitions, which uses one shared processing configuration.

## Purpose

Process experimental subgroups in separate runs when they need different settings
or have incompatible channel counts. Then explicitly combine their measurements
for comparison, without processing the images again.

## Proposed user workflow

1. Run each subgroup independently with its own `.pipeline/settings.toml`.
2. Choose an explicit **Merge quantification** action and select a parent folder.
3. Discover contributing runs, show which will contribute, and check table
   compatibility before writing a combined output.
4. Save a separate combined table, preserving all source results and run metadata.

Finding several nested `.pipeline` folders must not automatically switch normal
processing into a merge mode. Old run metadata can remain after acquisitions are
rearranged; folder structure alone does not establish merge intent.

## Input and identity rules

- Prefer current per-experiment quantification tables, using persisted experiment
  state to respect exclusion flags. Do not ingest both individual tables and their
  existing master tables, which would duplicate measurements.
- Discover each acquisition once even when candidate runs are nested. Establish
  its contributing run explicitly; overlapping roots must not double-count it.
- Add a source-run identifier and retain the original experiment/cell identifiers.
  Use their combination for globally unique identities; do not silently merge
  cells whose identifiers happen to match across runs.
- Record the contributing experiment identities and artifact revisions so later
  exclusion changes or source updates can be detected by a future merge refresh.
- The merge must not rewrite source identifiers, measurements, settings or flags.

## Compatibility

Different source channel counts alone do not prevent merging measurements.
Compatibility depends on measurement definitions, channel meanings, units,
compartments, and schema. Different valid measurement columns can be combined
with absent values left null; a shared column name with incompatible meaning
requires an explicit mapping or a clear error. Do not equate channels solely
because their source indices match.

Check currentness and availability separately from schema compatibility. Define
how missing, outdated and legacy tables are reported before implementation;
do not silently remeasure, run processing steps, or treat stale results as current.

## Responsibilities and implementation outline

- Keep GUI selection/presentation separate from a reusable merge operation.
- Reuse experiment discovery, persisted exclusions, artifact provenance and
  analysis table loading/aggregation utilities. Inspect their current contracts
  before adding a second aggregation implementation.
- Keep source validation independent of image-processing channel-count checks:
  this operation reads measurements rather than running one image pipeline.
- Finalize output location, metadata format, refresh behavior, and any future CLI
  entry point during implementation. Avoid overwriting an existing run master by
  default. Do not write combined results until compatibility checks succeed.

## Validation to add

- Runs with different channel counts and compatible measurements merge correctly.
- Missing columns remain null; conflicting channel meanings/units are reported.
- Excluded experiments are omitted; overlapping roots and existing masters do
  not cause duplicate rows.
- Repeated source experiment/cell names stay distinct through source-run identity.
- Source files remain unchanged, including on validation failure.
- Recorded membership/revisions reveal later source or exclusion changes.
