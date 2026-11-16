# Pipeline robustness and cancellation

Open work extracted and consolidated from the former `todos.txt`, 2026-11-16.
This document is a proposal, not a claim of implemented behaviour.

- [ ] Handle expected array-dimension incompatibilities in the shared pipeline
    for both CLI and GUI, e.g. tracking enabled for a single-frame image with
    no time axis (YX instead of TYX). Check axes/frame counts before calling
    the backend; mark the affected step as skipped with a clear reason in
    logs and progress reports, and continue steps whose inputs remain valid.
    Define downstream fallback/skip behavior when an output is unavailable
    (e.g. extraction can use segmentation masks after tracking is skipped).
    Do not suppress unrelated backend errors as dimension-related skips.
- [ ] Integrate the interactive coordinator with the full CPU/GPU conveyor pools
    if the conservative single-preparation/serial-downstream scheduler becomes
    a performance limitation.
- [ ] Define realistic cancellation guarantees for each processing backend.

Keep dimensional skips explicit and distinct from backend failures. Define and
validate downstream behaviour before allowing fallback to a different mask
producer. Conveyor integration is conditional on observed performance needs,
not an unconditional scheduler rewrite.
