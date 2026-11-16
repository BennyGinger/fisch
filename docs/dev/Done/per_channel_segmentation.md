# Per-channel segmentation settings

Completed checklist extracted from the former `todos.txt` on 2026-11-16.
This preserves recorded completion, not a new verification run.

Goal: segment multiple channels with independent Cellpose settings, using
the same configuration model in the GUI and CLI.
Status: implemented in pipeline, TOML, GUI, and SegTune.

GUI
- [x] Replace the shared channel/settings form with one section per channel.
- [x] Add + and − buttons beside each target channel. Adding copies the
    section's settings as a starting point; the last section cannot be removed.
- [x] Give each block its own channel selector, optional nuclear channel,
    denoising option, and Cellpose settings.
- [x] Tune the channel collection in SegTune. Select a summary row to revisit
    its controls; add the next unused channel or remove an existing row.
    Save current settings transfers the complete collection without closing.
- [x] Add compartment preview using shared bioimagequant distance maps, independent
    mask/image channels, per-tab colours, and unsaved-settings checks.
- [x] Optionally export mb/cyto FIScH masks; remove exports on compaction and rebuild
    them only when enabled in the saved extraction settings.
- [x] Keep execution, workers, ordering, and overwrite at the shared step level.

Configuration and CLI
- [x] Define repeated channel entries in TOML; the CLI continues to use the
    settings file without adding per-channel command-line flags.
- [x] Validate channel entries and reject duplicate target channels.

Supported TOML structure:

    [segment]
    enabled = true

    [segment.params]
    overwrite = false
    execution = "serial"

    [[segment.channels]]
    channel = "GFP"
    do_denoise = true

    [segment.channels.user_settings]
    model_type = "cyto3"
    diameter = 30

    [[segment.channels]]
    channel = "DAPI"
    do_denoise = false

    [segment.channels.user_settings]
    model_type = "nuclei"
    diameter = 15

Pipeline and provenance
- [x] Process channel entries in order with their respective settings.
- [x] Combine channel masks into the segmentation output while preserving
    channel identity.
- [x] Record the settings used for each channel in workflow provenance.
- [x] Ensure completion and overwrite decisions account for individual channels.
    A failure in any configured channel fails the step and no partial output is
    saved; this intentionally simple policy can be revisited later.

Validation and documentation
- [x] Test GUI add/remove, independent editing, and tuner apply/cancel behavior.
- [x] Test TOML save/load and CLI execution. Legacy settings are not supported.
- [x] Test that different channels receive their own settings and retain the
    correct output-channel mapping and provenance.
- [x] Update the settings template and GUI/CLI documentation with examples.
