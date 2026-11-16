# Run-wide channel-label renaming

Completed checklist extracted from the former `todos.txt` on 2026-11-16.
This preserves recorded completion, not a new verification run.

- [x] Inspect FIScH artifacts across the whole run, validate labels by source
    index, preview affected files, and rename through GUI or CLI.
- [x] Update known channel-bearing TIFF, Parquet, experiment-state, and saved
    settings fields while retaining pixels, lineage indices, and overlays.
- [x] Guard concurrent pipeline writes, reject stale previews, and restore
    earlier files if a later update fails.
