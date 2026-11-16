# Registration and background processing tuners

Completed checklist extracted from the former `todos.txt` on 2026-11-16.
This preserves recorded completion, not a new verification run.

- [x] Launch one shared Time/Channels registration tuner from either main-GUI
    settings section, initially selecting the corresponding tab. Load the GUI's
    current settings and selected experiment; lock run-directory browsing while
    retaining experiment selection within that run.

- [x] Offer standalone fisch-regtune with an optional image, --mode,
    --experiments-dir, and --settings. Keep standalone directory browsing.
    The pipeline CLI needs no tuner.

- [x] Reuse the classic experiment browser, navigation, Info dialog, and loading
    overlay, with Run preview, Save current settings, and Complete session to
    the right of the LUT. Parameter wheel changes require focus.

- [x] Support original/registered comparison and Composite overlay of the same
    frame/channel/Z plane: original grayscale, registered in its channel LUT;
    use magenta for the original when the registered image is grayscale.

- [x] Transfer accepted settings to the general main-GUI settings; expose Advanced
    settings only for changed manual overrides and preserve already-open
    sections. Standalone Save updates the supplied/nearest settings
    file or creates a template-based one. Presets set algorithm/method; manual
    choices restore a matching preset or select Custom. Top channel changes
    update the active tab's fitting/reference channel.

- [x] Save accepted per-experiment settings, optional crop and matching matrices
    outside image artifacts. Save current affects only the selected tab;
    Complete saves both tabs and closes without changing step-enabled states.
    Allow saving without preview: store settings/crop without stale matrices,
    and fit later in the pipeline. Validate fitting pixels before model reuse.

- [x] Keep original input virtual, project only fitting channels/frames across Z,
    and fit in a cancellable worker. Apply transforms only to requested preview
    planes, with a bounded cache instead of preparing a full output stack.

- [x] Release previews when switching experiments or closing. Repeated identical
    previews reuse results; parameter changes cannot save stale transforms.

- [x] Fit full time sequences for first/previous/mean strategies so accepted
    matrices cover every frame. Preview each tab independently on source data.
    Both tabs offer an opt-in manual fitting crop with zoom preview; disabling
    it restores full-image fitting. Lift crop transforms to full-image
    coordinates and retain unchanged output dimensions. Pin Resolved below
    scrolling settings and keep its size aligned across tabs.

- [x] Validate algorithm restoration, pixel equivalence, saved-model reuse, stale
    input rejection, settings transfer, cancellation, GUI/CLI launch, context
    matching, GUI settings priority and settings-only pipeline fitting.

- [x] Avoid waiting for all preview frames after fitting: display the requested
    frame/channel/Z plane on demand and cache only visited planes. Background
    preparation of a complete disk cache is unnecessary for this tuner.

- [x] Add an optional background-subtraction tuner with requested frame/channel/Z
    previews, reusable SMO, bounded result caching, general settings transfer,
    and independent GUI/CLI launch. Keep two actions (Run preview; Save and
    close), V for original/processed comparison, and an opt-in measurement box
    reporting both means. No background frame propagation in the initial version.

Further persistence of applied pipeline transforms and mask migration remain
in the [independent-mask plan](../independent_masks_registration_plan.md).
