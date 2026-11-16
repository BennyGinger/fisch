# Large-stack viewer handling

Open work extracted and consolidated from the former `todos.txt`, 2026-11-16.
This document is a proposal, not a claim of implemented behaviour.

- [ ] Instantiate only the active tool's image session; remove duplicate full-
    stack loading by hidden segmentation/reference/ROI sessions.

- [ ] Estimate decoded memory needs from shape and dtype, including channels,
    Z planes, masks, previews, and processing buffers, rather than frame count
    or compressed file size alone.

- [ ] Verify memory use and responsiveness on representative large stacks,
    including multi-channel and Z-stack examples and repeated tool switches.

The existing bounded plane caches, disk-backed edits and cleanup are recorded
in [completed viewer storage](Done/viewer_bounded_storage.md). Preserve common
small-stack responsiveness while testing multi-channel/Z data and tool switching.
