# Preprocessing overview

[Guide home](README.md)

Related: [Workflow](first_analysis.md) · [Shared settings](settings/common.md) · [REF/ROI workflow](reference_and_roi_masks.md)

Preprocessing corrects geometry and background before segmentation or measurement.
FIScH runs background subtraction, then channel registration, then time registration;
bypassed steps are omitted.

Tuners can open converted raw images before enabled upstream steps have produced
their outputs. They prefer the planned input when available; otherwise they use
the latest available image from enabled upstream steps, including converted raw.
A persistent status warning identifies this preview input. Hover over the status
to read the complete message, or select its text to copy it. The pipeline still
requires its configured inputs and does not use this preview fallback.

| Main settings tab | Dedicated settings page | Preview tool |
| --- | --- | --- |
| Frame-shift | [Frame-shift](settings/time_registration.md) | [Time-registration preview](tools/time_registration.md) |
| Channel-shift | [Channel-shift](settings/channel_registration.md) | [Channel-registration preview](tools/channel_registration.md) |
| Background subtraction | [Background subtraction](settings/background_subtraction.md) | [Background preview](tools/background_subtraction.md) |

Registration changes geometry and can require reviewing saved REF/ROI alignment.
Background subtraction changes intensities only. Preview tools save settings;
the pipeline writes full processed outputs.
