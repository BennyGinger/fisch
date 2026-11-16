# Tracking-editor follow-ups

Open work extracted and consolidated from the former `todos.txt`, 2026-11-16.
This document is a proposal, not a claim of implemented behaviour.

## Retained unfinished work

- [ ] Add redo and complete unsaved-change protection for close, source changes,
  and other operations that replace the current editing session.
- [ ] Add a replayable per-edit correction log. Existing compact operation/source
  provenance is not a replay log. Record relevant prompts/settings, accepted
  results and edit ordering without confusing initial clicks with final centroids.
- [ ] Evaluate explicit gap repair for migrating cells: mask interpolation and
  image-refined proposals must be previewed and accepted, not silently applied.
  Validate on representative irregular neutrophil/macrophage movies, large
  shape changes, touching cells, and faint structures.

Loading tracked movies, local micro-SAM prediction, brush correction,
merge/link/split/delete operations and accepted-mask centroids already exist.
Do not reimplement them from the older classical-predictor proposal.

Standalone saving, edited-artifact selection and quantification belong to the
[independent-mask plan](independent_masks_registration_plan.md). Static-only
propagation and temporal policy belong to the
[µSAM cleanup plan](microsam_tracking_cleanup.md). Motion-assisted tracking has
its [own research plan](motion_assisted_tracking.md).

Explicit point-observation annotation is a separate deferred feature, listed
in [deferred proposals](deferred_proposals.md); it is not required to save masks.
