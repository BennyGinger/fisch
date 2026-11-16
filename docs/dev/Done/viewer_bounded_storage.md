# Bounded viewer storage and caches

Completed checklist extracted from the former `todos.txt` on 2026-11-16.
This preserves recorded completion, not a new verification run.

- [x] Read viewer image/mask planes on demand through scope_io and PlaneStore,
    with caches bounded to eight planes and 64 MiB. Navigation does not load
    the complete movie; registration previews also cache requested planes.

- [x] Use temporary disk-backed storage for reference/ROI propagation previews,
    edited mask planes, and tracking save assembly. Registration previews
    resample only visited planes instead of preparing a second full stack.

- [x] Keep mask edits and undo snapshots separately from the original planes;
    avoid full-stack copies during navigation and unsaved-work bookkeeping.
    Existing-channel mask merging and segmentation volume previews still use
    their stack/volume routines; this does not imply every save is streaming.

- [x] Bound plane/trajectory preview caches and edit undo histories; release
    temporary edits/previews on replacement or close and discard cancelled
    preview results. Completed tracking-path caches persist with pruning.

[Remaining large-stack work](../large_stack_viewers_plan.md).
