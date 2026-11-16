# Independent masks, edited tracking, and registration updates

Status: agreed design, recorded 2026-11-16. Implementation is pending unless
explicitly described as existing behaviour below.

## Scope and related records

Keep manual tracking correction outside pipeline execution, make its saved
result selectable for quantification, and preserve independent masks through
intensity changes and registration rebuilds.

Related documents were checked before creating this plan:

- [FIScH 4 artifacts and provenance](Done/fits4_artifacts_plan.md): dependency checks,
  revisions, and the existing REF/ROI distinction between intensity and geometry.
- [Optional full rebuilding](Done/full_rebuild_plan.md): current rebuild behaviour,
  including manual alignment review for REF/ROI after registration changes.
- [µSAM tracking-editor cleanup](microsam_tracking_cleanup.md): inference and
  local temporal editing; not acquisition-wide registration migration.
- Completed [processing tuners](Done/processing_tuners.md) and
  [tracking-editor foundation](Done/tracking_editor_features.md): preview
  transform persistence and existing editor capabilities.

None covers this combined design. This plan extends the independent-mask policy
to edited tracking and proposes automatic geometry migration in place of manual
alignment review where supported. Earlier implementation records remain
historical descriptions, not evidence that these changes already work.

## Standalone editing and quantification

- Edit Track loads existing tracking, allows corrections to segmentation and
  track identities, and saves a complete independent edited artifact.
- Use the existing filenames `proc_track_edited.tif` and, when applicable,
  `proc_track_edited_filtered.tif`; preserve the original tracking artifact.
- Saving makes that result eligible for analysis, even if the user has only
  corrected part of an experiment. Accepting a local mask/split is distinct
  from saving the edited artifact to disk.
- Add a quantification parameter labelled **Use edited tracking when available**.
  Off selects original tracking. On selects edited tracking if available,
  otherwise original tracking. Analyse exactly one tracking mask per experiment;
  do not automatically generate parallel original/edited measurement tables.
- Record the actual chosen mask and revision in measurement provenance. A change
  of selected source invalidates existing measurements and requires remeasurement.
- Provide an explicit GUI way to discard edited tracking and return to automatic
  results. Refresh source discovery and invalidate affected measurements. Account
  for both edited filenames so deleting one does not unexpectedly activate another.
- Resolve which edited variant is active explicitly when both filenames exist;
  the precise UI/selection rule remains to be settled during implementation.
- Reuse ordinary quantification machinery. Do not introduce a separate analysis
  pipeline available only inside the editor.

## Artifact validity and checker policy

Only edited tracking, reference masks, and ROI masks are independent masks for
this policy. Automatic segmentation and tracking retain normal pipeline
dependency checks.

| Change | Independent edited/REF/ROI masks | Automatic segmentation/tracking | Measurements |
| --- | --- | --- | --- |
| Intensity-only upstream change, same geometry | Remain usable without changing pixels | Follow existing upstream invalidation | Recompute affected results |
| Segmentation rerun | Preserve edited tracking as a user-approved result | Automatic tracking becomes outdated | Recompute when actual inputs change |
| Tracking rerun | Preserve edited tracking as a user-approved result | Use normal tracking provenance | Recompute when actual inputs change |
| Registration geometry changes | Migrate existing masks as described below | Follow normal downstream invalidation | Recompute affected results |

Intensity changes can alter what a new segmentation run would detect, but do
not themselves move existing masks. Overwrite/rebuild choices must still let
users deliberately regenerate automatic results. Preserving independent masks
must not silently exempt automatic segmentation/tracking from invalidation.

Before rerunning automatic segmentation/tracking where edited tracking exists,
warn that the saved edited result remains preferred if the quantification
parameter is enabled. Users can discard it and restart correction after the
automatic rebuild. Its historical source remains recorded, without treating a
new automatic mask revision alone as invalidating the independent edited result.

The checker must distinguish intensity changes, geometry changes, independent
mask revisions, and automatic pipeline dependencies. This is a proposed extension
to the current checker, not a blanket bypass of provenance checks.

## Existing registration support

Code inspection found:

- All current StackAlign backends expose explicit `(N, 3, 3)` matrices:
  `scikit` supports translation; `cv2` and `pystackreg` support translation,
  rigid-body, and affine transforms. N is the frame or channel count.
- `RegisterModel.model` exports a detached model; `set_model()` restores it
  without fitting again.
- Registration tuning already saves matching accepted preview matrices,
  settings, and fitting signatures through `tasks/registration/tuned.py`.
  Acquisition-local paths are `.acquisition/tuning/<series>/registration/`
  with `time.npz` and `channel.npz`, using existing path helpers.
- Settings-only saves do not retain mismatched preview matrices.
- Normal processing checks fitting pixels, shape, axes, labels, settings, and
  fitting crop before reusing preview transforms. A different actual input
  requires fitting again. Preview channel fitting can include preceding time
  registration; actual pipeline compatibility must continue to be checked.
- Preview reuse avoids fitting again, not applying transforms to the full
  image stack and saving pipeline outputs. Preview display applies transforms
  to requested planes only.
- Fresh transforms fitted during ordinary pipeline processing are not yet
  consistently persisted as a record of the geometry actually published.
- Existing image resampling is not a label-preserving mask application API.

## One current registration transform set

Persist the transforms actually used by normal processing in the respective
acquisition's `.acquisition/` metadata, scoped per experiment/series. Keep this
applied geometry record distinct from accepted tuning/preview caches.

Each current set includes both channel and time registration, with disabled
stages represented as identity. Record channel labels, the reference channel
label, frame association, axes, shape, transform conventions, and the associated
registered image/geometry revision. Exact storage schema remains implementation
work; use existing acquisition path helpers rather than inventing a new root.

After a successful rebuild, retain only one current applied transform set.
Temporarily retain old and new sets during replacement; no permanent chain of
registration transforms is required by this plan.

Masks created from the current registered images already use current geometry.
For this single-current-set approach, all existing independent masks must be
advanced together whenever that geometry changes. Do not mark an unmigrated mask
as current. Legacy/unknown mask geometry needs explicit handling rather than an
assumption that it matches the current set.

## Migrating independent masks on registration overwrite

1. Retain the old applied transform set and existing outputs while preparing the
   new registration and its transform set.
2. Resolve each independent mask's channel and frame association. Construct the
   combined old-to-new mapping in actual pipeline order, accounting for both
   channel and time registration, rather than applying the new transforms alone.
3. Resample each mask once with the combined mapping and nearest-neighbour
   interpolation. Preserve integer IDs/binary labels and use background outside
   the image. Never blend track IDs with intensity interpolation.
4. Validate and publish registered images, migrated masks, geometry metadata,
   and checker state as one recoverable update. Geometry migration creates new
   mask revisions while preserving their derivation history.
5. Remove superseded active transforms only after every dependent independent
   mask has migrated successfully. On failure/cancellation, retain enough old
   data and transforms to recover; never leave mixed geometry presented as valid.
6. Invalidate affected measurements and ordinary downstream pipeline artifacts.

For example, if an old registration moved an object from x=100 to x=105 and the
new registration moves it to x=108, its existing mask needs a +3 correction,
not a further +8 shift. After successful migration, future masks use the new
geometry and the next overwrite starts from that geometry.

Matrices must use documented, normalised coordinate and mapping-direction
conventions before composition; equal array shape does not imply identical
backend conventions. Use actual workflow order, not the visual tab order.

A mask follows its associated image channel. The reference channel has an
identity channel transform, but time registration still applies. Changing the
reference channel can change that mapping too; do not permanently exempt masks
just because they once belonged to the reference channel. Cross-channel masks
need a defined channel association before automatic migration.

Analysis cropping is outside the present scope; display/fitting crops do not
change the output image extent. Nevertheless, registration can move labels
outside the field of view. Detect/report labels lost entirely. Nearest-neighbour
resampling preserves IDs, not exact boundaries or area. Repeated overwrites can
accumulate boundary changes; accept this limitation initially. Retaining a
permanent original mask and transforming from it is deferred.

## Implementation order and validation

1. Restore independent editor saving and explicit discard behaviour.
2. Add the quantification source parameter and shared input/provenance resolution.
3. Extend checker handling for independent masks and intensity-only changes.
4. Persist both applied registration models, preserving existing safe preview
   reuse and refitting when actual pipeline input differs.
5. Add combined label-preserving migration and recoverable replacement.

Focused validation should cover save/reopen, original-versus-edited selection
and fallback, partial experiment coverage, discard and measurement invalidation,
intensity-only preservation, and warnings after automatic mask rebuilds.
Registration coverage should include every supported backend/method, both stages
together, channel/reference changes, masks created between overwrites, identity
stages, repeated overwrites, preserved IDs, disappearing labels, and interrupted
publication. Until migration is implemented, geometry conflicts must remain
visible; documenting this plan does not authorise silent compatibility claims.
