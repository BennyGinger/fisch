"""Inspect conversion coverage and imported channel names without changing files."""

from collections.abc import Sequence
from pathlib import Path

from fisch.environment import constant as cst
from fisch.workflows.artifacts.provenance import read_metadata
from fisch.workflows.checks.models import RawInputReport
from fisch.workflows.experiments.model import ExperimentState


def needs_conversion(report: RawInputReport | None, states: Sequence[ExperimentState]) -> bool:
    """
    Require conversion when an active original lacks any expected converted series.
    """
    if report is None:
        return False
    for source in report.channel_counts:
        converted = [state for state in states if state.original_image == source
                     and (state.excluded or cst.StepName.CONVERT in state.completed_steps)]
        if len(converted) < len(report.frame_counts.get(source, (1,))):
            return True
    return False


def imported_channel_names(states: Sequence[ExperimentState]) -> dict[int, tuple[str, ...]]:
    """
    Collect names by original source index, including compacted image fallbacks.
    """
    names: dict[int, set[str]] = {}
    for state in states:
        if state.excluded:
            continue
        path: Path | None = next((candidate for kind in (cst.ARTI_IMG_RAW, cst.ARTI_IMG, cst.ARTI_TRACK, cst.ARTI_SEG)
                                 if (candidate := state.artifact(kind)) is not None and candidate.is_file()), None)
        if path is None:
            continue
        metadata = read_metadata(path).artifact
        for index, label in zip(metadata.artifact_channel_indices, metadata.channel_labels or []):
            names.setdefault(index, set()).add(label)
    return {index: tuple(sorted(values)) for index, values in names.items()}
