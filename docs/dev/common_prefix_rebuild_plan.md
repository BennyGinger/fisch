# Rebuild only the available common workflow prefix

Status: agreed proposal; implementation pending. Extracted during the
2026-11-16 developer-documentation review from the otherwise completed
[FIScH rename record](Done/fisch_rename_plan.md#agreed-future-behavior-rebuild-only-the-common-prefix).

## Problem and current behaviour

A historical numerical step may no longer be available, for example when its
segmentation implementation has been replaced. Current full-rebuild planning
stops with an explicit error before mutation. Retired manual interactions can
be skipped independently, but numerical producers cannot simply be bypassed.

## Agreed direction

- Reconstruct only the continuous common workflow prefix before the unavailable
  numerical step.
- Preserve old downstream results and mark them visibly outdated.
- Explain where rebuilding stopped and require the user to configure the current
  replacement and run the remaining workflow.
- Never jump from an upstream image directly into Tracking/Quantification across
  a missing producer.
- Make cleanup and completion reporting aware of partial execution, so the
  operation neither deletes preserved downstream results nor claims the entire
  experiment is current.

## Remaining implementation and validation

Extend rebuild planning and scoped execution with explicit stop boundaries;
align cleanup, provenance checks, and GUI/CLI reporting with those boundaries.
Cover unavailable numerical producers, preserved downstream files, clearly
outdated status, cancellation/failure, and subsequent completion after a user
configures the replacement. Continue to distinguish numerical producers from
retired manual interactions.

See the completed [full-rebuild record](Done/full_rebuild_plan.md) for the
implemented whole-workflow rebuilding baseline.
