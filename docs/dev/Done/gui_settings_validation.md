# GUI settings validation before starting a run

Completed checklist extracted from the former `todos.txt` on 2026-11-16.
This preserves recorded completion, not a new verification run.

- [x] Check critical settings for enabled steps before launching the pipeline.
    Missing conversion channel labels, channel-registration reference channel,
    segmentation channel, or tracking channel prevents leaving the affected
    step/phase and disables Run. Disabled steps do not require their unused
    settings, and the segmentation tuner may choose its initial channel.
