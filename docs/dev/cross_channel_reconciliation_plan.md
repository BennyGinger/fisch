# Cross-channel mask reconciliation and marker classification

Open work extracted and consolidated from the former `todos.txt`, 2026-11-16.
This document is a proposal, not a claim of implemented behaviour.

Goal: reconcile independently segmented marker channels into canonical objects,
optionally produce a combined normalization mask, and expose scalable marker-
detection classes in extraction tables. Preserve every original per-channel
mask unchanged.

- [ ] Add an optional reconciliation step after segmentation and before tracking.
    Keep object matching, object selection, and output geometry as separate
    settings rather than treating all three as one binary-mask operation.
- [ ] Match labelled objects across selected channels per frame. Record overlap
    pixels, intersection over the smaller object, IoU, and the source channel
    and label. Prefer one-to-one matches and explicitly flag ambiguous
    one-to-many or many-to-one cases instead of silently merging them.
- [ ] Assign a canonical object ID to matched and unmatched detections. Support
    two channels initially, but represent membership as channel-labelled data
    so the same implementation scales to three or more markers.
- [ ] Support object-selection rules: detected in any channel, every selected
    channel, exactly one channel, at least N channels, an exact channel
    combination, or exclusion of an exact combination.
- [ ] Configure combined-mask geometry independently from the selection rule:
    union of member masks, pixel intersection, or geometry from a selected
    anchor channel. Consider a pixel-level at-least-N/majority geometry later.
    A useful initial normalization default is any-channel inclusion with union
    geometry, retaining unmatched single-channel objects.
- [ ] Save a reconciled labelled TIFF only when a downstream workflow needs a
    canonical mask for tracking or normalization. Preserve channel membership,
    thresholds, geometry choice, conflicts, and source artifacts in provenance.
- [ ] Produce a canonical-object summary table with a typed list of detected
    channels plus readable `marker_pattern`, `marker_count`, `marker_class`,
    and `match_status` columns. Use scalable values such as `single` and
    `multiple`, rather than fixed double/triple-positive schemas.
- [ ] Produce a long-form membership table containing canonical object ID,
    source channel, source label, overlap measurements, match decision, and
    conflict state. Join the summary classification into extraction output so
    users can filter single-channel, multi-channel, at-least-N, or exact marker
    patterns without reconstructing the associations.
- [ ] Use "detected" terminology by default. Only label absence/presence as
    marker-negative/positive when the configured segmentation and scientific
    interpretation justify that claim.
- [ ] Keep numerical overlap/matching and its public table convention in the
    array-based quantification layer; FIScH owns settings, paths, scheduling,
    artifacts, and provenance. Validate the current `labelquant` API and schema
    before choosing the exact package/module boundary.
- [ ] Validate with matched masks of unequal size, contained masks, unmatched
    objects, crowded neighbours, ambiguous conflicts, and at least three
    channels. Confirm that classification is independent of union/intersection
    geometry and remains stable through tracking and extraction joins.
