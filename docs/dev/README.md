# Developer documentation

Architecture, development procedures, implementation plans, and audit records
for FIScH. For practical GUI instructions, start with the
[user guide](../user_guide/README.md). The [project README](../../README.md)
provides the overview, basic installation, and quick usage.

## Developer guides

[Guides](Guides/README.md) contains operational instructions, architecture, and
reference material. These describe existing functionality, not unfinished work.

- [Development setup](Guides/development_setup.md): manual environment setup and GPU configuration.
- [Releases](Guides/releases.md): automatic tags and GitHub Releases on stable version bumps.
- [Runtime and viewer internals](Guides/runtime_and_viewer_internals.md): execution,
  storage, caching, and interactive demonstration details moved from the README.
- [Software credits](Guides/software_credits.md): scientific methods, companion libraries,
  supporting dependencies, and citation guidance.
- [Workflow responsibilities](Guides/workflow_architecture.md): package boundaries and
  ownership of processing, artifacts, state, and file management.
- [Git and submodule cheatsheet](Guides/git_cheatsheet.md): maintaining the FIScH checkout
  and its numerical libraries.

## Open implementation plans

These plans contain unfinished work and remain at this level. Developer guides
live in `Guides/`; completed implementation records live in `Done/`.

- [Merge quantification](merge_quantification_plan.md): explicitly combine
  measurements from independently processed runs, including different channel counts.
- [Selective independent-mask deletion](independent_mask_deletion_plan.md):
  category filters, file selection, recoverable deletion, and the existing Reset action.
- [Independent masks and registration updates](independent_masks_registration_plan.md):
  standalone saving, quantification source selection, independent-mask validity,
  and registration transform persistence/migration.
- [Common-prefix rebuilding](common_prefix_rebuild_plan.md): rebuild only the
  available historical workflow prefix, preserving outdated downstream results.
- [User-guide screenshots](user_guide_screenshots.md): figures still to capture.
- [Pipeline robustness](pipeline_robustness_plan.md): dimension compatibility,
  cancellation guarantees, and conditional conveyor improvements.
- [Large-stack viewers](large_stack_viewers_plan.md): session consolidation,
  memory estimates, and representative dataset validation.
- [Cross-channel reconciliation](cross_channel_reconciliation_plan.md): canonical
  objects, marker membership, and optional combined-mask geometry.
- [Line profiles](line_profile_plan.md): drawing, numerical sampling, and export.
- [Deferred proposals](deferred_proposals.md): conditional Z identifiers,
  REF/ROI label suggestions, point observations, and tool shortcuts.

## Tracking development and research

- [µSAM tracking-editor cleanup](microsam_tracking_cleanup.md): integration
  responsibilities and recorded validation.
- [Tracking-editor follow-ups](tracking_editor_followups.md): redo, unsaved-work
  protection, replayable correction logs, and evaluated gap repair.
- [Motion-assisted tracking](motion_assisted_tracking.md): proposed work and
  evaluation directions.
- [Legacy BaxTrack context](Guides/baxter_legacy_context.md): historical integration
  details and source retrieval notes supporting the open motion-assisted plan.

## Completed implementation and audit records

- [Convert navigation and imported labels](Done/conversion_import_labels.md):
  complete-input startup checks, unconfirmed label hints and Next-driven relabeling.

Archived during the 2026-11-16 documentation review. Completion classification
uses the recorded implementation/validation evidence, checked against current
implementation modules and tests where practical. This was a documentation
review, not a new execution of the recorded test suites.

- [Artifact provenance and compaction](Done/fits4_artifacts_plan.md): five completed
  phases; later records supersede parts of its migration/rebuild policy.
- [Portable acquisitions](Done/portable_experiments_plan.md): six completed phases.
- [File-management actions](Done/file_management_actions_plan.md): implemented
  migration, relocation, updates, and processing boundaries.
- [Compaction, backups, and completion](Done/compaction_backups_completion_plan.md):
  completed storage, UI, and completion-reporting work.
- [Full rebuilding](Done/full_rebuild_plan.md): implemented whole-workflow rebuilding.
- [Experiment exclusion](Done/experiment_exclusion_plan.md): implemented persistence,
  active-series filtering, browser controls, and aggregation membership.
- [FIScH rename](Done/fisch_rename_plan.md): released rename/migration work. Its
  unfinished common-prefix proposal now has an
  [active plan](common_prefix_rebuild_plan.md).
- [Code-quality audit](Done/code_quality_audit.md): completed scoped audit/refactor.

### Completed feature checklists

- [GUI settings validation](Done/gui_settings_validation.md).
- [Run-wide channel-label renaming](Done/channel_label_renaming.md).
- [Static tracking post-processing](Done/static_tracking_postprocessing.md).
- [Tracking-editor foundation](Done/tracking_editor_features.md): existing operations;
  standalone GUI saving remains explicitly tracked as open work.
- [Per-channel segmentation](Done/per_channel_segmentation.md).
- [Processing tuners](Done/processing_tuners.md).
- [Bounded viewer storage](Done/viewer_bounded_storage.md).
- [Run metadata layout](Done/run_metadata_layout.md).

Records retain their original validation limits and superseded decisions;
archiving does not imply new platform or large-dataset verification. The
unfinished common-prefix proposal has its own active plan above.

The former `todos.txt` has been split into the focused plans above and completed
feature records in `Done/`. The superseded classical Add/Edit-first proposal and
duplicate implementation requests are no longer active backlog entries.

## User-facing reference

- [Analysis identifiers and measurement columns](../user_guide/analysis_identifiers.md).

## Reference

Existing material moved from the project README; it has not been rewritten into a new walkthrough.

### Repository maintenance

FIScH uses Git submodules and a uv workspace. The practical commands for
cloning, updating, editing, adding, and removing submodules are collected in
the [Git and submodule cheatsheet](Guides/git_cheatsheet.md).
