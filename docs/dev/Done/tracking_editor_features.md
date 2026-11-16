# Tracking editor: implemented foundation

Completed checklist extracted from the former `todos.txt` on 2026-11-16.
This preserves recorded completion, not a new verification run.

- [x] Build a dedicated FIScH tracking viewer/editor, reusing the existing image
    viewer's navigation and interaction patterns but with a multi-label
    track overlay and track-aware session/model (not the binary mask canvas).
- [x] Implement local Add/Edit proposals with headless micro-SAM, positive and
    negative prompts, an expected-diameter crop, explicit prediction/acceptance,
    manual brush corrections, and protection of other track IDs. Accepted masks
    update centroids and trajectory displays. Split retains its separate
    geometry/intensity/watershed predictor. See microsam_tracking_cleanup.md.
- [x] Start an empty tracking session from proc_array.tif, allocate track IDs,
    and accept masks across frames. Save through the existing edited-tracking
    outputs (proc_track_edited.tif or proc_track_edited_filtered.tif).
- [x] Inspect and correct existing tracking: merge/link tracks, split a history
    after the selected frame, unlink detections, delete a mask or whole track,
    split a mask, and undo accepted edits. Save compact steps.edit_track.params
    provenance with source artifact, operations used, mask/image channels,
    filter condition, timestamp, and FIScH version.



The completion above records editor/session capabilities. Standalone GUI saving
is currently blocked by pipeline-request wiring; it is not completed by the
existence of the save function. See the active
[independent-mask plan](../independent_masks_registration_plan.md) and
[editor follow-ups](../tracking_editor_followups.md).
The superseded classical Add/Edit-first proposal is not retained as open work;
headless micro-SAM is the implemented Add/Edit backend.
