"""Prepare one rollback-protected relabel operation across portable acquisitions."""

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from fisch.channel_labels.discovery import file_fingerprint, inspect_files, files_to_update, validate_labels
from fisch.channel_labels.documents import labels_in_table, labels_in_workflow_meta
from fisch.channel_labels.model import LabelPlan
from fisch.environment import constant as cst
from fisch.environment.paths import is_internal_path
from fisch.workflows.experiments import active_states, discover_saved_states
from fisch.workflows.artifacts.provenance import read_metadata


@dataclass(frozen=True)
class ConversionLabelUpdate:
    """Describe processed files to relabel before converting fresh inputs."""

    plan: LabelPlan
    proposed: dict[int, str]
    mapping: dict[str, str]
    acquisition_count: int


def prepare_conversion_labels(root: Path, labels: list[str]) -> ConversionLabelUpdate | None:
    """
    Combine acquisition-local mappings without assuming imported names agree.
    """
    if not labels or any(not label.strip() for label in labels) or len(set(labels)) != len(labels):
        raise ValueError('Provide unique, non-empty effective channel labels.')
    states = active_states(discover_saved_states(root))
    acquisitions = sorted({state.original_image.parent for state in states
                           if cst.StepName.CONVERT in state.completed_steps})
    if not acquisitions:
        return None
    plans: list[LabelPlan] = []
    mappings: dict[Path, tuple[tuple[str, str], ...]] = {}
    destinations: dict[str, set[str]] = defaultdict(set)
    source_labels: dict[int, str] = {}
    changed_acquisitions = 0
    for acquisition in acquisitions:
        plan = inspect_files(acquisition, include_settings=False)
        proposed = {index: labels[index] for index, _ in plan.labels if index < len(labels)}
        validate_labels(plan, proposed)
        mapping = tuple((old, proposed[index]) for index, old in plan.labels)
        for old, new in mapping:
            destinations[old].add(new)
        for index, old in plan.labels:
            source_labels.setdefault(index, old)
        changed_acquisitions += bool(files_to_update(plan, proposed))
        mappings.update({path: mapping for path in plan.files})
        plans.append(plan)
    common = {old: next(iter(values)) for old, values in destinations.items() if len(values) == 1}
    tables = [path for (_, name) in cst.MASTER_TABLES for path in root.rglob(name)
              if not is_internal_path(path, root)]
    table_labels: list[tuple[Path, frozenset[str]]] = []
    for path in tables:
        present = labels_in_table(path) | labels_in_workflow_meta(read_metadata(path).custom_metadata)
        ambiguous = {old for old in present if len(destinations.get(old, set())) > 1}
        if ambiguous:
            raise ValueError(f'{path}: combined table has ambiguous imported channel names {sorted(ambiguous)}. '
                             'Update labels in the contributing runs separately before combining this table.')
        mappings[path] = tuple(common.items())
        table_labels.append((path, present))
    files = tuple(dict.fromkeys(path for plan in plans for path in plan.files))
    combined = LabelPlan(root,
                         tuple(sorted(source_labels.items())),
                         tuple(path for plan in plans for path in plan.tiffs),
                         tuple(dict.fromkeys([*(path for plan in plans for path in plan.tables), *tables])),
                         (),
                         tuple(path for plan in plans for path in plan.states),
                         tuple(item for plan in plans for item in plan.file_labels) + tuple(table_labels),
                         tuple((path, file_fingerprint(path)) for path in dict.fromkeys((*files, *tables))),
                         tuple(mappings.items()),
                         conversion_labels=tuple(labels),
                         )
    proposed = {index: labels[index] for index in source_labels}
    return ConversionLabelUpdate(combined, proposed, common, changed_acquisitions)
