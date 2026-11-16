# Deferred development proposals

Open work extracted and consolidated from the former `todos.txt`, 2026-11-16.
This document is a proposal, not a claim of implemented behaviour.

These ideas remain conditional or speculative. They are preserved for future
review, not promoted to immediate implementation requirements.

## Per-Z-plane analysis identifiers

- [ ] If extraction gains independent per-Z-plane measurements, include the
    explicit plane index in cell_id to distinguish labels reused across planes.
    Current extraction max-projects Z and deliberately omits it from IDs.
    Do not use a moving 3D object's centroid_z as an identity component.
    See [analysis identifiers](../user_guide/analysis_identifiers.md) for the current experiment/cell ID convention.

## Consistent reference/ROI label suggestions

- [ ] Consider using the first finalized experiment as the naming template for
    the rest of the run, separately for reference and ROI masks.
- [ ] Later experiments would choose only labels established in the first one.
    Its finalized mask counts would replace the initial expected counts for
    subsequent experiments. Do not implement this restriction yet.
- [ ] Decide how to handle an unrepresentative first experiment, missing structures,
    skipped labels, existing masks with different names, and deliberate exceptions.
    Consider suggestions first, with an optional strict mode rather than a hard lock.

## Point-observation annotation

- [ ] Consider an independent `(frame, x, y, track ID)` annotation store if a
  point-tracking workflow is needed. A clicked seed may propose a mask, but
  accepted masks determine displayed trajectory centroids. Do not confuse seed
  observations with final segmentation-derived coordinates.

## Tool launch shortcuts

- [ ] Consider separate executable shortcuts/icons for the tools if users need
  them. Existing GUI and command-line launchers are already available.
