# Convert

[Guide home](../README.md)

Related: [Main GUI](../runs_and_settings.md) · [Channels and labels](../channels_and_labels.md) · [Shared settings](common.md) · [Manage files](../tools/manage_files.md)

Convert source ND2/TIFF images into the managed FIScH images used by later steps.

## Inputs and controls

| Setting / action | Practical meaning |
| --- | --- |
| Channel / Expected colour / Label | Enter optional labels in source order. Blank cells use detected/default names; colours come from acquisition metadata where available. |
| Export channels | Keep the channels needed downstream; multiple selection is allowed. |
| Z projection | Max, mean, sum, or standard deviation combines Z planes. None preserves the Z stack. |
| Compression | TIFF storage compression; this is separate from image processing. |
| Edit labels… | Opens Manage files for a separate existing-file rename. Convert's Next also applies changed labels to processed acquisitions. |

## Convert and navigate the processing pages

The main interface has two pages. A run with **any active input still needing conversion** opens on **Convert**;
**Next** performs conversion only and moves to the processing page after it
finishes successfully. Reopening a run whose active inputs are all converted opens the
processing page directly, with **Preprocess** selected. **Back** returns to
Convert. An unchanged **Next** returns to processing without another conversion;
changed labels are applied to existing processed files before fresh inputs are
converted. Label changes alone do not require reconverting existing image pixels.
Use Overwrite when you intend to repeat conversion itself.
Having existing processed acquisitions never enables overwrite implicitly.
With overwrite off, saved conversion state and existing outputs are reused;
settings differences go through the normal checker/review before reprocessing.

## Imported labels and Next

Fresh-only runs have no imported-name suggestions. When fresh and processed
acquisitions are mixed, consistent imported names appear as hints such as **GFP?**
in the status and empty Label cells. Conflicting names at a source-channel
position show **Mixed?**; hover to see them. Hints are not values, are never saved
with a question mark, and are not applied automatically.

- Type the suggested name to confirm it. Matching processed labels are retained.
- Enter another name to apply it to both fresh and processed acquisitions.
- Leave a cell empty to use the detected/default name, not the imported hint.

**Next** first updates any changed processed labels through the same rollback-
protected operation as Edit labels, then converts fresh inputs. Images, masks,
per-experiment tables, unambiguous combined-table references and saved provenance
are updated together; raw inputs and pixel values are preserved. If relabeling
fails, conversion does not start. Orange console messages announce the update
and confirm it, including at conversion completion. A failed later conversion
does not undo an already successful label update.

This also works after returning with **Back** in an existing run. Changing fields
or saving settings alone does not relabel files. **Run pipeline** on the processing
page does not perform this label-edit operation. Source positions must represent
the same biological channels across acquisitions; confirming this is your
responsibility. Different channel counts are reported before conversion.

Before conversion, check source channel order, the chosen/default labels, and which channels to export. See [Channels and labels](../channels_and_labels.md) for count warnings, generic fallback names, and the choices offered downstream.

Files with the same stem in the same folder receive extension-specific
acquisition folders (for example, `sample_nd2/sample.nd2` and
`sample_tif/sample.tif`), with a console log message and no popup. Original
filenames are preserved. Matching stems in different subfolders do not need
this adjustment. Existing or conflicting destination folders block conversion.

Settings changed while conversion is running apply to the next conversion.

## Output

Conversion writes `proc_array_raw.tif` for each series and records completed
artifacts in experiment state. See Shared processing settings for Include,
Overwrite, Execution and Workers.
