# Line-profile measurement

Open work extracted and consolidated from the former `todos.txt`, 2026-11-16.
This document is a proposal, not a claim of implemented behaviour.

Goal: provide a tool for users to generate and visualize line profiles from bioimagequant images.
- [ ] Implement line drawing and selection interface.
- [ ] Compute intensity profiles along the drawn line for each channel.
- [ ] Display the line profile in a separate plot window.
- [ ] Allow exporting the line profile data to a parquet file.
- [ ] Support updating the profile dynamically when the line is adjusted.

This means intensity along a user-drawn line, not the existing area-intensity
profile display or distance-to-reference analysis. Keep numerical sampling in
the array-based analysis layer and drawing/export orchestration in FIScH.
