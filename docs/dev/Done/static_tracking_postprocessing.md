# Static-cell tracking post-processing

Completed checklist extracted from the former `todos.txt` on 2026-11-16.
This preserves recorded completion, not a new verification run.

- [x] Implemented a FIScH-owned, tracker-agnostic static-mask postprocessor.
    It restores stable identities with a temporal super-mask built from pixels
    present in at least half of each label's observed frames,
    removes masks that differ from each track's consensus shape, discards
    tracks below the minimum-appearances threshold, fills internal gaps, and
    optionally extrapolates the first and last valid masks to the sequence
    boundaries. Weak, ambiguous, and unmatched identities are cleared before
    filling. Existing valid masks are protected; collision-clipped reconstructions
    must retain sufficient IoU with their intended shape. Tiny remnants are
    rejected, and tracks that cannot be completed are removed.
    Settings are integrated into the tracking task, TOML configuration, and
    the GUI's basic settings. The implementation remains independent of
    `tracklink`, allowing future tracking backends to reuse it unchanged.
