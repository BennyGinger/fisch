# Selective deletion of independent masks

Status: agreed UI direction, recorded 2026-11-16. Implementation pending.

## Purpose and scope

Add a deletion subsection to Manage files for independent masks only:
reference masks, ROI masks, and edited tracking masks. Do not extend this
action to images, automatic segmentation, automatic tracking, or arbitrary
files.

Place the existing Reset button in the same subsection as a separate action.
Reset is already implemented: retain its existing meaning, scope, confirmation,
and behaviour. This plan does not introduce a new reset operation or make Reset
depend on the deletion filters/selection.

Related records:

- [File-management actions](Done/file_management_actions_plan.md): existing Manage
  files responsibilities and operations.
- [Independent masks and registration updates](independent_masks_registration_plan.md):
  edited tracking selection, independent-mask validity, and discard behaviour.

## Proposed layout

1. Category controls at the top: **Reference**, **ROI**, and **Edited tracking**.
   Use independent toggles/checkboxes; multiple categories may be active.
2. A directory browser below, following the main GUI's folder hierarchy but
   showing only files belonging to active categories. Hide branches without
   matching files. Display filenames so selections are explicit.
3. Controls for **Select all matching files** and **Clear selection**.
4. A red **Delete selected** button with a selected-file count.
5. The existing **Reset** action, visually distinct from selective deletion.

## Selection behaviour

- Allow manual selection of individual matching files, preferably with
  checkboxes separate from the browser's highlighted/navigation row.
- Checking a folder selects matching descendants; show partial selection for
  folders containing both selected and unselected matching files.
- Select all operates on all matching files under the browser's current root,
  including collapsed branches, not unrelated files or inactive categories.
- Changing category filters deselects files that become hidden. Never delete
  a selection the user can no longer inspect in the filtered tree.
- Disable deletion when nothing is selected. Keep the count and button state
  in sync with manual selection, bulk selection, and category changes.
- Edited tracking covers both `proc_track_edited.tif` and
  `proc_track_edited_filtered.tif`. Show them individually; category selection
  alone must not silently add an unselected sibling file to deletion.
- Discover active independent artifacts using existing artifact naming and
  inventory rules. Exclude internal backups/history from the active tree.

## Deletion and recovery

The agreed direction is selective deletion; recoverable backup is preferred
over irreversible removal. Reuse the existing acquisition-local backup/history
mechanism where suitable rather than introducing a separate backup system.

Before applying deletion, show a compact review of the exact selected paths,
counts by category, and where recovery is available. The action must operate
on that reviewed selection and verify that files still match the reviewed
inventory. If they changed, refresh the review rather than deleting new data
under old selections.

Retain recoverable copies before removing active files. A backup failure must
not result in losing the corresponding active file. Report partial failures
clearly and refresh the tree to show what actually remains.

## State and analysis consequences

- Refresh the Manage files browser, main run inventory, tool availability, and
  affected state after deletion.
- Let the shared checker reassess analyses that depend on deleted REF/ROI masks.
- Removing edited tracking may change the quantification source to original
  tracking when **Use edited tracking when available** is enabled. Measurements
  from the removed source must no longer appear current; require remeasurement.
- If another edited variant remains, make the remaining source discoverable and
  follow the explicit active-variant policy from the independent-mask plan.
- Preserve truthful provenance/history; do not rewrite existing measurements as
  though they had used the replacement source.
- Do not automatically rerun numerical processing as a side effect of deletion.

## Implementation and validation

First inspect and reuse the existing Manage files browser, Reset action,
artifact inventory, and backup services. Keep selection/filter UI separate from
the operation that reviews, backs up, deletes, and refreshes state.

Validate category combinations, individual/folder/bulk selection, collapsed
branches, hidden-selection removal, both edited variants, empty selections,
backup exclusion, cancellation, files changed after review, backup/deletion
failures, and checker refresh. Verify that unrelated files remain untouched
and the existing Reset behaviour is unchanged.

This document records a plan only; it does not claim that selective deletion or
the proposed quantification source parameter is already implemented.
