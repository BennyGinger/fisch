# Convert navigation and imported channel labels

Implemented 2026-11-17. This extends the [portable acquisition rules](portable_experiments_plan.md).

- Open Convert if any active original lacks its expected converted series.
  Excluded series do not force conversion; finding one processed image is not
  enough to skip Convert.
- Fresh-only inputs have no imported-name suggestions. Mixed fresh/processed
  inputs display names by source index as `GFP?` or `Mixed?`. Names are collected
  from retained converted/compacted images; suggestions remain display-only.
- Convert's Next resolves the requested labels using existing color/C1 defaults.
  Matching results are untouched. Changed labels use the existing writer guard,
  fingerprint checks, per-file atomic writes and whole-operation rollback.
- Acquisition-local plans are combined with per-file mappings so differently
  labeled imports can be unified. TIFF channels retain source indices. State,
  image and table provenance record effective conversion labels. Table channel
  fields and affected cell IDs use the existing rename implementation.
- Combined tables can be relabeled when their old labels map unambiguously.
  Conflicting meanings for the same old label in a combined table block the
  operation before any files change; update the contributing runs separately.
  This is not the future cross-run quantification merge feature.
- Existing nested run settings remain untouched. The destination draft follows
  unambiguous channel-reference changes and retains the requested Convert values;
  normal Next persistence saves destination settings before conversion.
- Orange console messages announce and confirm processed-acquisition relabeling.
  Relabel failure prevents conversion. A subsequent conversion failure does not
  roll back a completed label update.
- Save settings and Run pipeline do not invoke relabeling. Existing Edit labels
  remains available as a separate action.
- GUI launches never set `force_conversion` merely because prepared images exist.
  Explicit Overwrite and reviewed processing changes govern replacement; matching
  converted states pass through `decide_run` and are skipped. Real GUI launch
  tests exercise both Next and Run pipeline and verify existing image bytes,
  timestamps and backup inventories remain unchanged while fresh inputs convert.
- Read-only GUI inventory does not call absent masters outdated. Execution still
  plans missing masters. Settings comparison uses effective channel labels and
  preserves genuine projection, compression and other processing differences.

Regression coverage lives in `tests/gui/test_conversion_imports.py`, alongside
the existing channel-label API, settings-conflict, channel-choice and run-root tests.

Initial folder inspection now uses the existing background-task Processing
dialog. Saved settings are loaded before one inventory scan; source metadata
results are applied to widgets on the GUI thread. Label-only updates refresh the
remembered label signature without accepting projection/compression changes as
already converted. Tests cover responsive inspection and those navigation boundaries.
